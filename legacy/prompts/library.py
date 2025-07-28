"""Prompt library and template management system for players."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from enum import Enum
import json
import hashlib

from src.prompts.template_system import PromptTemplate, TemplateLevel, TemplateCategory


class PromptVisibility(Enum):
    """Visibility levels for saved prompts."""
    PRIVATE = "private"  # Only owner can see
    FRIENDS = "friends"  # Friends list can see
    PUBLIC = "public"  # Everyone can see
    TEAM = "team"  # Team members can see


class PromptTag(Enum):
    """Common tags for prompts."""
    SPEED_OPTIMIZED = "speed_optimized"
    ACCURACY_FOCUSED = "accuracy_focused"
    CREATIVE = "creative"
    BEGINNER_FRIENDLY = "beginner_friendly"
    ADVANCED = "advanced"
    TOURNAMENT_READY = "tournament_ready"
    EXPERIMENTAL = "experimental"
    VERIFIED = "verified"  # Verified by experts


@dataclass
class SavedPrompt:
    """A prompt saved in the library."""
    prompt_id: str
    owner_id: str
    title: str
    content: str
    game_name: str
    template_id: Optional[str]  # If based on a template
    visibility: PromptVisibility
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    version: int = 1
    parent_id: Optional[str] = None  # For version tracking
    
    # Performance metrics
    usage_count: int = 0
    total_score: float = 0.0
    avg_score: float = 0.0
    win_rate: float = 0.0
    best_score: float = 0.0
    
    # Social metrics
    likes: int = 0
    shares: int = 0
    forks: int = 0
    comments: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def calculate_effectiveness(self) -> float:
        """Calculate overall effectiveness score."""
        if self.usage_count == 0:
            return 0.0
        
        # Weighted combination of metrics
        score = (
            self.avg_score * 0.4 +
            self.win_rate * 0.3 +
            min(1.0, self.usage_count / 20) * 0.2 +  # Usage popularity
            min(1.0, self.likes / 10) * 0.1  # Social validation
        )
        return score
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/API."""
        return {
            "prompt_id": self.prompt_id,
            "owner_id": self.owner_id,
            "title": self.title,
            "content": self.content,
            "game_name": self.game_name,
            "template_id": self.template_id,
            "visibility": self.visibility.value,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
            "parent_id": self.parent_id,
            "usage_count": self.usage_count,
            "avg_score": self.avg_score,
            "win_rate": self.win_rate,
            "best_score": self.best_score,
            "likes": self.likes,
            "shares": self.shares,
            "forks": self.forks,
            "effectiveness": self.calculate_effectiveness()
        }


@dataclass
class PromptCollection:
    """A collection of prompts (like a playlist)."""
    collection_id: str
    owner_id: str
    name: str
    description: str
    prompt_ids: List[str]
    visibility: PromptVisibility
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    
    # Collection metrics
    followers: int = 0
    total_uses: int = 0
    
    def add_prompt(self, prompt_id: str):
        """Add a prompt to the collection."""
        if prompt_id not in self.prompt_ids:
            self.prompt_ids.append(prompt_id)
            self.updated_at = datetime.utcnow()
    
    def remove_prompt(self, prompt_id: str):
        """Remove a prompt from the collection."""
        if prompt_id in self.prompt_ids:
            self.prompt_ids.remove(prompt_id)
            self.updated_at = datetime.utcnow()


class PromptLibrary:
    """Manages player prompt libraries and sharing."""
    
    def __init__(self):
        self.prompts: Dict[str, SavedPrompt] = {}  # prompt_id -> SavedPrompt
        self.user_libraries: Dict[str, List[str]] = {}  # user_id -> [prompt_ids]
        self.collections: Dict[str, PromptCollection] = {}
        self.templates: Dict[str, PromptTemplate] = {}  # Shared templates
        self.social_graph: Dict[str, Set[str]] = {}  # user_id -> friend_ids
        self.prompt_index: Dict[str, List[str]] = {  # Indexes for search
            "by_game": {},
            "by_tag": {},
            "by_template": {}
        }
    
    def save_prompt(
        self,
        owner_id: str,
        title: str,
        content: str,
        game_name: str,
        visibility: PromptVisibility = PromptVisibility.PRIVATE,
        tags: Optional[List[str]] = None,
        template_id: Optional[str] = None,
        parent_id: Optional[str] = None
    ) -> str:
        """Save a new prompt to the library."""
        # Generate prompt ID
        prompt_id = self._generate_prompt_id(owner_id, content)
        
        # Check for duplicates
        if prompt_id in self.prompts:
            # Update existing instead
            return self.update_prompt(prompt_id, owner_id, content=content)
        
        # Create saved prompt
        prompt = SavedPrompt(
            prompt_id=prompt_id,
            owner_id=owner_id,
            title=title,
            content=content,
            game_name=game_name,
            template_id=template_id,
            visibility=visibility,
            tags=tags or [],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            parent_id=parent_id
        )
        
        # Handle versioning
        if parent_id and parent_id in self.prompts:
            parent = self.prompts[parent_id]
            prompt.version = parent.version + 1
        
        # Store prompt
        self.prompts[prompt_id] = prompt
        
        # Update user library
        if owner_id not in self.user_libraries:
            self.user_libraries[owner_id] = []
        self.user_libraries[owner_id].append(prompt_id)
        
        # Update indexes
        self._index_prompt(prompt)
        
        return prompt_id
    
    def _generate_prompt_id(self, owner_id: str, content: str) -> str:
        """Generate unique prompt ID."""
        hash_input = f"{owner_id}:{content}:{datetime.utcnow().isoformat()}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:12]
    
    def _index_prompt(self, prompt: SavedPrompt):
        """Add prompt to search indexes."""
        # By game
        if prompt.game_name not in self.prompt_index["by_game"]:
            self.prompt_index["by_game"][prompt.game_name] = []
        self.prompt_index["by_game"][prompt.game_name].append(prompt.prompt_id)
        
        # By tag
        for tag in prompt.tags:
            if tag not in self.prompt_index["by_tag"]:
                self.prompt_index["by_tag"][tag] = []
            self.prompt_index["by_tag"][tag].append(prompt.prompt_id)
        
        # By template
        if prompt.template_id:
            if prompt.template_id not in self.prompt_index["by_template"]:
                self.prompt_index["by_template"][prompt.template_id] = []
            self.prompt_index["by_template"][prompt.template_id].append(prompt.prompt_id)
    
    def update_prompt(
        self,
        prompt_id: str,
        user_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        tags: Optional[List[str]] = None,
        visibility: Optional[PromptVisibility] = None
    ) -> str:
        """Update an existing prompt."""
        if prompt_id not in self.prompts:
            raise ValueError(f"Prompt {prompt_id} not found")
        
        prompt = self.prompts[prompt_id]
        
        # Check ownership
        if prompt.owner_id != user_id:
            raise PermissionError("Only owner can update prompt")
        
        # Create new version if content changed significantly
        if content and content != prompt.content:
            # Save as new version
            new_id = self.save_prompt(
                owner_id=user_id,
                title=title or prompt.title,
                content=content,
                game_name=prompt.game_name,
                visibility=visibility or prompt.visibility,
                tags=tags or prompt.tags,
                template_id=prompt.template_id,
                parent_id=prompt_id
            )
            return new_id
        
        # Update in place for minor changes
        if title:
            prompt.title = title
        if tags is not None:
            prompt.tags = tags
        if visibility:
            prompt.visibility = visibility
        
        prompt.updated_at = datetime.utcnow()
        
        # Re-index if tags changed
        if tags is not None:
            self._reindex_prompt(prompt)
        
        return prompt_id
    
    def _reindex_prompt(self, prompt: SavedPrompt):
        """Re-index a prompt after updates."""
        # Remove from old indexes
        for tag_list in self.prompt_index["by_tag"].values():
            if prompt.prompt_id in tag_list:
                tag_list.remove(prompt.prompt_id)
        
        # Re-add to indexes
        self._index_prompt(prompt)
    
    def fork_prompt(
        self,
        prompt_id: str,
        user_id: str,
        new_title: Optional[str] = None
    ) -> str:
        """Fork someone else's prompt."""
        if prompt_id not in self.prompts:
            raise ValueError(f"Prompt {prompt_id} not found")
        
        original = self.prompts[prompt_id]
        
        # Check visibility
        if not self._can_access_prompt(user_id, original):
            raise PermissionError("Cannot access this prompt")
        
        # Create fork
        fork_title = new_title or f"Fork of {original.title}"
        new_id = self.save_prompt(
            owner_id=user_id,
            title=fork_title,
            content=original.content,
            game_name=original.game_name,
            visibility=PromptVisibility.PRIVATE,  # Start as private
            tags=original.tags + ["forked"],
            template_id=original.template_id,
            parent_id=prompt_id
        )
        
        # Update original's fork count
        original.forks += 1
        
        # Add metadata
        self.prompts[new_id].metadata["forked_from"] = prompt_id
        self.prompts[new_id].metadata["forked_at"] = datetime.utcnow().isoformat()
        
        return new_id
    
    def _can_access_prompt(self, user_id: str, prompt: SavedPrompt) -> bool:
        """Check if user can access a prompt."""
        # Owner always has access
        if user_id == prompt.owner_id:
            return True
        
        # Check visibility
        if prompt.visibility == PromptVisibility.PUBLIC:
            return True
        elif prompt.visibility == PromptVisibility.FRIENDS:
            return user_id in self.social_graph.get(prompt.owner_id, set())
        elif prompt.visibility == PromptVisibility.TEAM:
            # Would check team membership
            return False
        
        return False
    
    def search_prompts(
        self,
        user_id: str,
        game_name: Optional[str] = None,
        tags: Optional[List[str]] = None,
        template_id: Optional[str] = None,
        owner_id: Optional[str] = None,
        min_effectiveness: Optional[float] = None,
        sort_by: str = "effectiveness",
        limit: int = 50
    ) -> List[SavedPrompt]:
        """Search for prompts with filters."""
        results = []
        
        # Start with all accessible prompts
        if owner_id:
            # Specific owner's prompts
            prompt_ids = self.user_libraries.get(owner_id, [])
        elif game_name and game_name in self.prompt_index["by_game"]:
            prompt_ids = self.prompt_index["by_game"][game_name]
        else:
            prompt_ids = list(self.prompts.keys())
        
        # Filter
        for prompt_id in prompt_ids:
            if prompt_id not in self.prompts:
                continue
                
            prompt = self.prompts[prompt_id]
            
            # Access check
            if not self._can_access_prompt(user_id, prompt):
                continue
            
            # Game filter
            if game_name and prompt.game_name != game_name:
                continue
            
            # Tag filter
            if tags and not any(tag in prompt.tags for tag in tags):
                continue
            
            # Template filter
            if template_id and prompt.template_id != template_id:
                continue
            
            # Effectiveness filter
            if min_effectiveness and prompt.calculate_effectiveness() < min_effectiveness:
                continue
            
            results.append(prompt)
        
        # Sort
        if sort_by == "effectiveness":
            results.sort(key=lambda p: p.calculate_effectiveness(), reverse=True)
        elif sort_by == "recent":
            results.sort(key=lambda p: p.updated_at, reverse=True)
        elif sort_by == "popular":
            results.sort(key=lambda p: p.usage_count, reverse=True)
        elif sort_by == "score":
            results.sort(key=lambda p: p.avg_score, reverse=True)
        
        return results[:limit]
    
    def get_recommendations(
        self,
        user_id: str,
        game_name: str,
        context: Optional[Dict[str, Any]] = None,
        limit: int = 5
    ) -> List[SavedPrompt]:
        """Get prompt recommendations for a user and game."""
        recommendations = []
        
        # Get user's prompt history
        user_prompts = [
            self.prompts[pid] for pid in self.user_libraries.get(user_id, [])
            if pid in self.prompts and self.prompts[pid].game_name == game_name
        ]
        
        if user_prompts:
            # Find similar successful prompts
            avg_score = sum(p.avg_score for p in user_prompts) / len(user_prompts)
            
            # Look for prompts slightly better than user's average
            target_effectiveness = min(avg_score + 0.1, 0.9)
            
            candidates = self.search_prompts(
                user_id=user_id,
                game_name=game_name,
                min_effectiveness=target_effectiveness,
                sort_by="effectiveness",
                limit=limit * 2
            )
            
            # Filter out user's own prompts
            recommendations = [
                p for p in candidates 
                if p.owner_id != user_id
            ][:limit]
        else:
            # New user - recommend popular beginner-friendly prompts
            recommendations = self.search_prompts(
                user_id=user_id,
                game_name=game_name,
                tags=[PromptTag.BEGINNER_FRIENDLY.value],
                sort_by="popular",
                limit=limit
            )
        
        return recommendations
    
    def record_usage(
        self,
        prompt_id: str,
        score: float,
        won: bool,
        game_details: Optional[Dict[str, Any]] = None
    ):
        """Record usage of a prompt."""
        if prompt_id not in self.prompts:
            return
        
        prompt = self.prompts[prompt_id]
        
        # Update metrics
        prompt.usage_count += 1
        prompt.total_score += score
        prompt.avg_score = prompt.total_score / prompt.usage_count
        
        if won:
            wins = int(prompt.win_rate * (prompt.usage_count - 1))
            prompt.win_rate = (wins + 1) / prompt.usage_count
        else:
            wins = int(prompt.win_rate * (prompt.usage_count - 1))
            prompt.win_rate = wins / prompt.usage_count
        
        if score > prompt.best_score:
            prompt.best_score = score
        
        prompt.updated_at = datetime.utcnow()
    
    def create_collection(
        self,
        owner_id: str,
        name: str,
        description: str,
        prompt_ids: Optional[List[str]] = None,
        visibility: PromptVisibility = PromptVisibility.PRIVATE,
        tags: Optional[List[str]] = None
    ) -> str:
        """Create a new prompt collection."""
        collection_id = f"col_{owner_id}_{len(self.collections)}"
        
        collection = PromptCollection(
            collection_id=collection_id,
            owner_id=owner_id,
            name=name,
            description=description,
            prompt_ids=prompt_ids or [],
            visibility=visibility,
            tags=tags or [],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.collections[collection_id] = collection
        return collection_id
    
    def share_prompt(
        self,
        prompt_id: str,
        sharer_id: str,
        share_with: List[str],
        message: Optional[str] = None
    ) -> bool:
        """Share a prompt with other users."""
        if prompt_id not in self.prompts:
            return False
        
        prompt = self.prompts[prompt_id]
        
        # Check access
        if not self._can_access_prompt(sharer_id, prompt):
            return False
        
        # Update share count
        prompt.shares += 1
        
        # In real implementation, would notify recipients
        # For now, just track the share
        if "shares" not in prompt.metadata:
            prompt.metadata["shares"] = []
        
        prompt.metadata["shares"].append({
            "sharer_id": sharer_id,
            "recipients": share_with,
            "message": message,
            "shared_at": datetime.utcnow().isoformat()
        })
        
        return True
    
    def export_prompts(
        self,
        user_id: str,
        prompt_ids: Optional[List[str]] = None,
        format: str = "json"
    ) -> str:
        """Export prompts for backup or sharing."""
        if prompt_ids is None:
            # Export all user's prompts
            prompt_ids = self.user_libraries.get(user_id, [])
        
        prompts_data = []
        for prompt_id in prompt_ids:
            if prompt_id in self.prompts:
                prompt = self.prompts[prompt_id]
                if prompt.owner_id == user_id:
                    prompts_data.append(prompt.to_dict())
        
        if format == "json":
            return json.dumps({
                "exported_at": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "prompts": prompts_data
            }, indent=2)
        
        # Could support other formats
        return ""