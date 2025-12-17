"""
Matching Engine for ENSA HR Module
Handles student-internship matching and supervisor-project matching using AI embeddings
"""
import logging
import math
from typing import List, Dict, Any, Tuple, Optional
from odoo import api, models, _

_logger = logging.getLogger(__name__)


class MatchingEngine:
    """AI-powered matching engine for students and internships"""
    
    def __init__(self, ai_service):
        """
        Initialize matching engine
        
        Args:
            ai_service: AIService instance for generating embeddings
        """
        self.ai_service = ai_service
    
    def calculate_skill_match(self, student_skills: List[str], required_skills: List[str]) -> float:
        """
        Calculate skill match score using set intersection
        
        Args:
            student_skills: List of student skills
            required_skills: List of required skills
            
        Returns:
            Match score (0-100)
        """
        if not student_skills or not required_skills:
            return 0.0
        
        # Normalize skills (lowercase, strip)
        student_set = set(skill.lower().strip() for skill in student_skills)
        required_set = set(skill.lower().strip() for skill in required_skills)
        
        # Calculate Jaccard similarity
        intersection = len(student_set & required_set)
        union = len(student_set | required_set)
        
        if union == 0:
            return 0.0
        
        jaccard_score = (intersection / union) * 100
        
        # Bonus for having all required skills
        if required_set.issubset(student_set):
            jaccard_score = min(jaccard_score + 10, 100)
        
        return round(jaccard_score, 2)
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors (pure Python)"""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
            
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm_a = math.sqrt(sum(a * a for a in vec1))
        norm_b = math.sqrt(sum(b * b for b in vec2))
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
            
        return dot_product / (norm_a * norm_b)
    
    def calculate_semantic_match(self, text1: str, text2: str) -> float:
        """
        Calculate semantic similarity using embeddings
        
        Args:
            text1: First text (e.g., student interests)
            text2: Second text (e.g., internship description)
            
        Returns:
            Similarity score (0-100)
        """
        try:
            # Generate embeddings
            emb1 = self.ai_service.generate_embeddings(text1)
            emb2 = self.ai_service.generate_embeddings(text2)
            
            if not emb1 or not emb2:
                return 0.0
            
            # Calculate cosine similarity using pure Python
            similarity = self._cosine_similarity(emb1, emb2)
            
            # Convert to percentage
            return round(similarity * 100, 2)
            
        except Exception as e:
            _logger.error(f"Semantic match error: {str(e)}")
            return 0.0
    
    def match_student_to_internship(
        self,
        student_data: Dict[str, Any],
        internship_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive match score between student and internship
        
        Args:
            student_data: Student information
            internship_data: Internship requirements
            
        Returns:
            Match results with score and breakdown
        """
        # Extract data
        student_skills = student_data.get('skills', [])
        student_interests = student_data.get('interests', '')
        student_performance = student_data.get('avg_score', 0)
        student_level = student_data.get('level', '')
        
        required_skills = internship_data.get('required_skills', [])
        internship_description = internship_data.get('description', '')
        internship_type = internship_data.get('type', '')
        required_level = internship_data.get('required_level', '')
        
        # Calculate skill match (40% weight)
        skill_score = self.calculate_skill_match(student_skills, required_skills)
        
        # Calculate semantic match for interests vs description (30% weight)
        semantic_score = self.calculate_semantic_match(
            f"{student_interests} {' '.join(student_skills)}",
            f"{internship_description} {internship_type}"
        )
        
        # Performance bonus (20% weight)
        performance_score = min((student_performance / 10) * 100, 100)
        
        # Level match (10% weight)
        level_score = 100 if student_level.lower() == required_level.lower() else 50 if required_level == '' else 30
        
        # Weighted total
        total_score = (
            skill_score * 0.4 +
            semantic_score * 0.3 +
            performance_score * 0.2 +
            level_score * 0.1
        )
        
        return {
            'total_score': round(total_score, 2),
            'skill_match': skill_score,
            'semantic_match': semantic_score,
            'performance_bonus': performance_score,
            'level_match': level_score,
            'recommendation': self._get_recommendation(total_score)
        }
    
    def match_supervisor_to_project(
        self,
        supervisor_data: Dict[str, Any],
        project_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate match between supervisor and student project
        
        Args:
            supervisor_data: Supervisor information
            project_data: Project requirements
            
        Returns:
            Match results
        """
        supervisor_expertise = supervisor_data.get('expertise', '')
        supervisor_skills = supervisor_data.get('skills', '')
        supervisor_availability = supervisor_data.get('current_projects', 0)
        
        project_domain = project_data.get('domain', '')
        project_tech = project_data.get('technology_stack', '')
        
        # Semantic match for expertise vs project domain
        expertise_match = self.calculate_semantic_match(
            f"{supervisor_expertise} {supervisor_skills}",
            f"{project_domain} {project_tech}"
        )
        
        # Availability score (fewer projects = better)
        availability_score = max(100 - (supervisor_availability * 20), 20)
        
        # Weighted score
        total_score = expertise_match * 0.7 + availability_score * 0.3
        
        return {
            'total_score': round(total_score, 2),
            'expertise_match': expertise_match,
            'availability_score': availability_score,
            'recommendation': self._get_recommendation(total_score)
        }
    
    def predict_success_probability(
        self,
        student_data: Dict[str, Any],
        internship_data: Dict[str, Any],
        match_score: float
    ) -> float:
        """
        Predict internship success probability
        
        Args:
            student_data: Student information
            internship_data: Internship details
            match_score: Pre-calculated match score
            
        Returns:
            Success probability (0-1)
        """
        # Factors affecting success
        student_performance = student_data.get('avg_score', 5) / 10  # 0-1
        student_consistency = student_data.get('performance_trend') == 'improving'  # Boolean
        internship_has_supervisor = internship_data.get('has_supervisor', False)  # Boolean
        match_quality = match_score / 100  # 0-1
        
        # Weighted probability
        base_probability = (
            student_performance * 0.3 +
            match_quality * 0.4 +
            (0.2 if student_consistency else 0.1) +
            (0.15 if internship_has_supervisor else 0.05)
        )
        
        # Cap between 0.1 and 0.95
        return max(0.1, min(base_probability, 0.95))
    
    def rank_candidates(
        self,
        candidates: List[Dict[str, Any]],
        opportunity: Dict[str, Any],
        match_type: str = 'internship'
    ) -> List[Dict[str, Any]]:
        """
        Rank multiple candidates for an opportunity
        
        Args:
            candidates: List of candidate data
            opportunity: Opportunity data
            match_type: 'internship' or 'project'
            
        Returns:
            Ranked list with match scores
        """
        results = []
        
        for candidate in candidates:
            if match_type == 'internship':
                match_result = self.match_student_to_internship(candidate, opportunity)
            else:
                match_result = self.match_supervisor_to_project(candidate, opportunity)
            
            results.append({
                'candidate_id': candidate.get('id'),
                'candidate_name': candidate.get('name'),
                **match_result
            })
        
        # Sort by total score (descending)
        results.sort(key=lambda x: x['total_score'], reverse=True)
        
        return results
    
    def _get_recommendation(self, score: float) -> str:
        """Get recommendation based on score"""
        if score >= 80:
            return 'Excellent Match - Highly Recommended'
        elif score >= 65:
            return 'Good Match - Recommended'
        elif score >= 50:
            return 'Fair Match - Consider with review'
        else:
            return 'Weak Match - Not Recommended'


class OdooMatchingEngine(models.AbstractModel):
    """Odoo model wrapper for Matching Engine"""
    _name = 'ensa.matching.engine'
    _description = 'Matching Engine Service'
    
    @api.model
    def get_matching_engine(self):
        """Get configured matching engine instance"""
        ai_service = self.env['ensa.ai.service'].get_ai_service()
        return MatchingEngine(ai_service)
    
    @api.model
    def match_internship(self, student_id: int, internship_id: int) -> Dict[str, Any]:
        """
        Match a student to an internship (Odoo-friendly wrapper)
        
        Args:
            student_id: Student record ID
            internship_id: Internship record ID
            
        Returns:
            Match results
        """
        # This will be implemented fully when we enhance internship model
        engine = self.get_matching_engine()
        
        # Placeholder - actual implementation will fetch from student/internship models
        student_data = {'skills': [], 'interests': '', 'avg_score': 7}
        internship_data = {'required_skills': [], 'description': ''}
        
        return engine.match_student_to_internship(student_data, internship_data)
