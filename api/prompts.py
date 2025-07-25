"""Prompt library endpoints."""
from http.server import BaseHTTPRequestHandler
import json
from urllib.parse import urlparse, parse_qs
from . import supabase_db as db

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query_params = parse_qs(parsed_path.query)
        
        # Search/list prompts
        if path == '/api/prompts':
            query = query_params.get('q', [''])[0]
            game_type = query_params.get('game_type', [None])[0]
            tags = query_params.get('tags', [])
            
            prompts = db.search_prompts(query=query, game_type=game_type, tags=tags)
            
            self.send_json_response({
                "prompts": prompts,
                "total": len(prompts)
            })
            
        # Get specific prompt
        elif path.startswith('/api/prompts/') and len(path.split('/')) == 4:
            prompt_id = path.split('/')[-1]
            # Get prompt by ID
            if hasattr(db, 'supabase') and db.supabase:
                result = db.supabase.table('prompts').select('*').eq('id', prompt_id).execute()
                prompt = result.data[0] if result.data else None
            else:
                # Fallback to JSON
                prompts = db.load_json(db.PROMPTS_FILE, {})
                prompt = prompts.get(prompt_id)
            
            if prompt:
                self.send_json_response(prompt)
            else:
                self.send_error(404, "Prompt not found")
                
        # Get featured prompts
        elif path == '/api/prompts/featured':
            all_prompts = db.search_prompts()
            # Sort by likes and usage
            featured = sorted(all_prompts, 
                            key=lambda p: p.get("likes", 0) + p.get("usage_count", 0), 
                            reverse=True)[:6]
            
            self.send_json_response({
                "featured": featured
            })
            
        # Get prompt categories/tags
        elif path == '/api/prompts/tags':
            all_prompts = db.search_prompts()
            tags = {}
            
            for prompt in all_prompts:
                for tag in prompt.get("tags", []):
                    tags[tag] = tags.get(tag, 0) + 1
                    
            # Sort by frequency
            sorted_tags = sorted(tags.items(), key=lambda x: x[1], reverse=True)
            
            self.send_json_response({
                "tags": [{"name": tag, "count": count} for tag, count in sorted_tags]
            })
            
        # Get prompts by author
        elif path.startswith('/api/prompts/author/'):
            author = path.split('/')[-1]
            all_prompts = db.search_prompts()
            author_prompts = [p for p in all_prompts if p.get("author") == author]
            
            self.send_json_response({
                "prompts": author_prompts,
                "author": author
            })
            
        else:
            self.send_error(404)
    
    def do_POST(self):
        path = self.path
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)
        
        # Create new prompt
        if path == '/api/prompts':
            prompt_data = {
                "name": data.get("name", "Untitled Prompt"),
                "description": data.get("description", ""),
                "content": data.get("content", ""),
                "game_type": data.get("game_type", "minesweeper"),
                "author": data.get("author", "anonymous"),
                "tags": data.get("tags", []),
                "variables": data.get("variables", {}),
                "example_output": data.get("example_output", ""),
                "is_public": data.get("is_public", True)
            }
            
            prompt_id = db.save_prompt(prompt_data)
            
            self.send_json_response({
                "success": True,
                "prompt_id": prompt_id,
                "prompt": db.load_json(db.PROMPTS_FILE, {}).get(prompt_id)
            })
            
        # Like/upvote prompt
        elif path.startswith('/api/prompts/') and path.endswith('/like'):
            prompt_id = path.split('/')[-2]
            # Get current prompt
            if hasattr(db, 'supabase') and db.supabase:
                result = db.supabase.table('prompts').select('*').eq('id', prompt_id).execute()
                prompt = result.data[0] if result.data else None
                
                if prompt:
                    new_likes = prompt.get("likes", 0) + 1
                    db.supabase.table('prompts').update({
                        'likes': new_likes
                    }).eq('id', prompt_id).execute()
                    
                    self.send_json_response({
                        "success": True,
                        "likes": new_likes
                    })
                else:
                    self.send_error(404, "Prompt not found")
            else:
                # Fallback to JSON
                prompts = db.load_json(db.PROMPTS_FILE, {})
                
                if prompt_id in prompts:
                    prompts[prompt_id]["likes"] = prompts[prompt_id].get("likes", 0) + 1
                    db.save_json(db.PROMPTS_FILE, prompts)
                    
                    self.send_json_response({
                        "success": True,
                        "likes": prompts[prompt_id]["likes"]
                    })
                else:
                    self.send_error(404, "Prompt not found")
                
        # Fork/duplicate prompt
        elif path.startswith('/api/prompts/') and path.endswith('/fork'):
            prompt_id = path.split('/')[-2]
            # Get original prompt
            if hasattr(db, 'supabase') and db.supabase:
                result = db.supabase.table('prompts').select('*').eq('id', prompt_id).execute()
                original = result.data[0] if result.data else None
            else:
                prompts = db.load_json(db.PROMPTS_FILE, {})
                original = prompts.get(prompt_id)
            
            if original:
                # Create a copy
                fork_data = original.copy()
                fork_data["name"] = f"{fork_data['name']} (Fork)"
                fork_data["author"] = data.get("author", "anonymous")
                fork_data["forked_from"] = prompt_id
                fork_data["likes"] = 0
                fork_data["usage_count"] = 0
                
                new_prompt_id = db.save_prompt(fork_data)
                
                # Get the newly created prompt
                new_prompt = None
                if hasattr(db, 'supabase') and db.supabase:
                    result = db.supabase.table('prompts').select('*').eq('id', new_prompt_id).execute()
                    new_prompt = result.data[0] if result.data else None
                else:
                    prompts = db.load_json(db.PROMPTS_FILE, {})
                    new_prompt = prompts.get(new_prompt_id)
                
                self.send_json_response({
                    "success": True,
                    "prompt_id": new_prompt_id,
                    "prompt": new_prompt
                })
            else:
                self.send_error(404, "Prompt not found")
                
        # Test prompt
        elif path.startswith('/api/prompts/') and path.endswith('/test'):
            prompt_id = path.split('/')[-2]
            # Get prompt
            if hasattr(db, 'supabase') and db.supabase:
                result = db.supabase.table('prompts').select('*').eq('id', prompt_id).execute()
                prompt = result.data[0] if result.data else None
            else:
                prompts = db.load_json(db.PROMPTS_FILE, {})
                prompt = prompts.get(prompt_id)
            
            if not prompt:
                self.send_error(404, "Prompt not found")
                return
                
            test_context = data.get("context", {})
            
            # Simulate prompt testing
            # In real implementation, this would run the prompt with the model
            test_result = {
                "prompt_id": prompt_id,
                "test_context": test_context,
                "rendered_prompt": self._render_prompt(prompt["content"], test_context),
                "execution_time": 0.523,
                "model_response": "This is a simulated response for testing purposes.",
                "success": True
            }
            
            # Increment usage count
            new_usage_count = prompt.get("usage_count", 0) + 1
            if hasattr(db, 'supabase') and db.supabase:
                db.supabase.table('prompts').update({
                    'usage_count': new_usage_count
                }).eq('id', prompt_id).execute()
            else:
                prompts = db.load_json(db.PROMPTS_FILE, {})
                if prompt_id in prompts:
                    prompts[prompt_id]["usage_count"] = new_usage_count
                    db.save_json(db.PROMPTS_FILE, prompts)
            
            self.send_json_response(test_result)
            
        else:
            self.send_error(404)
    
    def do_PUT(self):
        path = self.path
        
        # Update prompt
        if path.startswith('/api/prompts/') and len(path.split('/')) == 4:
            prompt_id = path.split('/')[-1]
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            updates = json.loads(post_data)
            
            # Update prompt
            if hasattr(db, 'supabase') and db.supabase:
                from datetime import datetime
                updates["updated_at"] = datetime.utcnow().isoformat()
                result = db.supabase.table('prompts').update(updates).eq('id', prompt_id).execute()
                if result.data:
                    self.send_json_response({
                        "success": True,
                        "prompt": result.data[0]
                    })
                else:
                    self.send_error(404, "Prompt not found")
            else:
                # Fallback to JSON
                prompts = db.load_json(db.PROMPTS_FILE, {})
                if prompt_id in prompts:
                    from datetime import datetime
                    prompts[prompt_id].update(updates)
                    prompts[prompt_id]["updated_at"] = datetime.utcnow().isoformat()
                    db.save_json(db.PROMPTS_FILE, prompts)
                    
                    self.send_json_response({
                        "success": True,
                        "prompt": prompts[prompt_id]
                    })
                else:
                    self.send_error(404, "Prompt not found")
        else:
            self.send_error(404)
    
    def do_DELETE(self):
        path = self.path
        
        # Delete prompt
        if path.startswith('/api/prompts/') and len(path.split('/')) == 4:
            prompt_id = path.split('/')[-1]
            
            # Delete prompt
            if hasattr(db, 'supabase') and db.supabase:
                result = db.supabase.table('prompts').delete().eq('id', prompt_id).execute()
                if result.data:
                    self.send_json_response({
                        "success": True,
                        "message": "Prompt deleted"
                    })
                else:
                    self.send_error(404, "Prompt not found")
            else:
                # Fallback to JSON
                prompts = db.load_json(db.PROMPTS_FILE, {})
                if prompt_id in prompts:
                    del prompts[prompt_id]
                    db.save_json(db.PROMPTS_FILE, prompts)
                    
                    self.send_json_response({
                        "success": True,
                        "message": "Prompt deleted"
                    })
                else:
                    self.send_error(404, "Prompt not found")
        else:
            self.send_error(404)
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def send_json_response(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())
    
    def _render_prompt(self, template: str, context: dict) -> str:
        """Render a prompt template with variables."""
        result = template
        for key, value in context.items():
            result = result.replace(f"{{{key}}}", str(value))
        return result