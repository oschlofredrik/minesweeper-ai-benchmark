"""Evaluation system endpoints."""
from http.server import BaseHTTPRequestHandler
import json
from urllib.parse import urlparse, parse_qs
from . import supabase_db as db

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query_params = parse_qs(parsed_path.query)
        
        # List evaluations
        if path == '/api/evaluations':
            game_type = query_params.get('game_type', [None])[0]
            evaluations = db.list_evaluations(game_type=game_type)
            self.send_json_response(evaluations)
            
        # Get specific evaluation
        elif path.startswith('/api/evaluations/') and len(path.split('/')) == 4:
            eval_id = path.split('/')[-1]
            evaluation = db.get_evaluation(eval_id)
            if evaluation:
                self.send_json_response(evaluation)
            else:
                self.send_error(404, "Evaluation not found")
                
        # Marketplace endpoints
        elif path == '/api/evaluations/marketplace':
            # Get featured/popular evaluations
            all_evals = db.list_evaluations()
            marketplace = {
                "featured": all_evals[:3],  # Top 3 by usage
                "categories": {
                    "reasoning": [e for e in all_evals if "reasoning" in e.get("tags", [])],
                    "efficiency": [e for e in all_evals if "efficiency" in e.get("tags", [])],
                    "accuracy": [e for e in all_evals if "accuracy" in e.get("tags", [])]
                },
                "total": len(all_evals)
            }
            self.send_json_response(marketplace)
            
        # Get evaluations for a game
        elif path.startswith('/api/evaluations/games/'):
            game_id = path.split('/')[-1]
            # In a real implementation, we'd track which evaluations are attached to games
            self.send_json_response({
                "game_id": game_id,
                "evaluations": []  # Placeholder
            })
            
        else:
            self.send_error(404)
    
    def do_POST(self):
        path = self.path
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)
        
        # Create new evaluation
        if path == '/api/evaluations':
            eval_data = {
                "name": data.get("name", "Untitled Evaluation"),
                "description": data.get("description", ""),
                "game_type": data.get("game_type", "minesweeper"),
                "author": data.get("author", "anonymous"),
                "metrics": data.get("metrics", []),
                "weights": data.get("weights", {}),
                "tags": data.get("tags", []),
                "is_public": data.get("is_public", True)
            }
            
            eval_id = db.create_evaluation(eval_data)
            evaluation = db.get_evaluation(eval_id)
            
            self.send_json_response({
                "success": True,
                "evaluation_id": eval_id,
                "evaluation": evaluation
            })
            
        # Test evaluation
        elif path.startswith('/api/evaluations/') and path.endswith('/test'):
            eval_id = path.split('/')[-2]
            evaluation = db.get_evaluation(eval_id)
            
            if not evaluation:
                self.send_error(404, "Evaluation not found")
                return
                
            # Simulate test results
            test_results = {
                "evaluation_id": eval_id,
                "test_game": data.get("test_game", {}),
                "scores": {
                    metric: {"score": 0.75 + (i * 0.05), "details": f"Test result for {metric}"}
                    for i, metric in enumerate(evaluation.get("metrics", []))
                },
                "overall_score": 0.82,
                "execution_time": 0.234
            }
            
            self.send_json_response(test_results)
            
        # Import evaluation from marketplace
        elif path.startswith('/api/evaluations/marketplace/') and path.endswith('/import'):
            eval_id = path.split('/')[-2]
            source_eval = db.get_evaluation(eval_id)
            
            if not source_eval:
                self.send_error(404, "Evaluation not found")
                return
                
            # Create a copy for the user
            import_data = source_eval.copy()
            import_data["name"] = f"{import_data['name']} (Imported)"
            import_data["is_imported"] = True
            import_data["source_id"] = eval_id
            
            new_eval_id = db.create_evaluation(import_data)
            
            self.send_json_response({
                "success": True,
                "evaluation_id": new_eval_id,
                "message": "Evaluation imported successfully"
            })
            
        # Rate evaluation
        elif path.startswith('/api/evaluations/marketplace/') and path.endswith('/rate'):
            eval_id = path.split('/')[-2]
            rating = data.get("rating", 5)
            
            evaluation = db.get_evaluation(eval_id)
            if not evaluation:
                self.send_error(404, "Evaluation not found")
                return
                
            # Update rating (simplified - in real app would track individual ratings)
            ratings = evaluation.get("ratings", [])
            ratings.append(rating)
            avg_rating = sum(ratings) / len(ratings)
            
            # Update the evaluation with new rating
            evaluation["ratings"] = ratings
            evaluation["rating"] = avg_rating
            
            # For Supabase, we'd update directly, for JSON fallback this is handled internally
            if hasattr(db, 'supabase') and db.supabase:
                db.supabase.table('evaluations').update({
                    'ratings': ratings,
                    'rating': avg_rating
                }).eq('id', eval_id).execute()
            else:
                # Fallback to JSON update
                evaluations = db.load_json(db.EVALUATIONS_FILE, {})
                if eval_id in evaluations:
                    evaluations[eval_id]["ratings"] = ratings
                    evaluations[eval_id]["rating"] = avg_rating
                    db.save_json(db.EVALUATIONS_FILE, evaluations)
            
            self.send_json_response({
                "success": True,
                "new_rating": avg_rating,
                "total_ratings": len(ratings)
            })
            
        # Attach evaluations to game
        elif path.startswith('/api/evaluations/games/') and path.endswith('/attach'):
            game_id = path.split('/')[-2]
            eval_ids = data.get("evaluation_ids", [])
            
            # In a real implementation, we'd track this association
            self.send_json_response({
                "success": True,
                "game_id": game_id,
                "attached_evaluations": eval_ids
            })
            
        else:
            self.send_error(404)
    
    def do_PUT(self):
        path = self.path
        
        # Update evaluation
        if path.startswith('/api/evaluations/') and len(path.split('/')) == 4:
            eval_id = path.split('/')[-1]
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            updates = json.loads(post_data)
            
            # Update evaluation
            if hasattr(db, 'supabase') and db.supabase:
                from datetime import datetime
                updates["updated_at"] = datetime.utcnow().isoformat()
                result = db.supabase.table('evaluations').update(updates).eq('id', eval_id).execute()
                success = bool(result.data)
            else:
                # Fallback to JSON
                evaluations = db.load_json(db.EVALUATIONS_FILE, {})
                if eval_id in evaluations:
                    from datetime import datetime
                    evaluations[eval_id].update(updates)
                    evaluations[eval_id]["updated_at"] = datetime.utcnow().isoformat()
                    db.save_json(db.EVALUATIONS_FILE, evaluations)
                    success = True
                else:
                    success = False
                
            if success:
                evaluation = db.get_evaluation(eval_id)
                self.send_json_response({
                    "success": True,
                    "evaluation": evaluation
                })
            else:
                self.send_error(404, "Evaluation not found")
        else:
            self.send_error(404)
    
    def do_DELETE(self):
        path = self.path
        
        # Delete evaluation
        if path.startswith('/api/evaluations/') and len(path.split('/')) == 4:
            eval_id = path.split('/')[-1]
            
            # Delete evaluation
            if hasattr(db, 'supabase') and db.supabase:
                result = db.supabase.table('evaluations').delete().eq('id', eval_id).execute()
                success = bool(result.data)
            else:
                # Fallback to JSON
                evaluations = db.load_json(db.EVALUATIONS_FILE, {})
                if eval_id in evaluations:
                    del evaluations[eval_id]
                    db.save_json(db.EVALUATIONS_FILE, evaluations)
                    success = True
                else:
                    success = False
            
            if success:
                self.send_json_response({
                    "success": True,
                    "message": "Evaluation deleted"
                })
            else:
                self.send_error(404, "Evaluation not found")
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