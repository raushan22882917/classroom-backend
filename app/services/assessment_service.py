"""Assessment and content generation services for Magic Learn platform"""

import asyncio
import json
import time
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import google.generativeai as genai
import os
import random
from dataclasses import dataclass, asdict

from app.models.magic_learn import (
    AssessmentRequest, AssessmentResponse,
    ContentGenerationRequest, ContentGenerationResponse,
    DifficultyLevel, AnalysisType
)

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


@dataclass
class Question:
    """Data class for assessment question"""
    question_id: str
    question_text: str
    question_type: str  # multiple_choice, true_false, short_answer, essay, calculation
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    points: int = 1
    difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    topic: Optional[str] = None
    learning_objective: Optional[str] = None


@dataclass
class Assessment:
    """Data class for complete assessment"""
    assessment_id: str
    title: str
    description: str
    subject: str
    topic: str
    difficulty_level: DifficultyLevel
    questions: List[Question]
    time_limit_minutes: int
    total_points: int
    passing_score: int
    created_at: datetime
    learning_objectives: List[str]
    scoring_rubric: Dict[str, Any]


class AssessmentService:
    """Service for generating and managing assessments"""
    
    def __init__(self):
        self.assessments = {}
        self.question_bank = {}
        self.assessment_results = {}
    
    async def generate_assessment(self, request: AssessmentRequest) -> AssessmentResponse:
        """Generate a comprehensive assessment"""
        
        try:
            assessment_id = str(uuid.uuid4())
            
            # Generate questions based on request
            questions = await self._generate_questions(request)
            
            # Calculate assessment parameters
            time_limit = await self._calculate_time_limit(questions, request.difficulty_level)
            total_points = sum(q.points for q in questions)
            passing_score = int(total_points * 0.7)  # 70% passing score
            
            # Generate learning objectives
            learning_objectives = await self._generate_learning_objectives(request)
            
            # Create scoring rubric
            scoring_rubric = await self._create_scoring_rubric(questions, request.difficulty_level)
            
            # Create assessment
            assessment = Assessment(
                assessment_id=assessment_id,
                title=f"{request.subject} - {request.topic} Assessment",
                description=f"Assessment covering {request.topic} at {request.difficulty_level.value} level",
                subject=request.subject,
                topic=request.topic,
                difficulty_level=request.difficulty_level,
                questions=questions,
                time_limit_minutes=time_limit,
                total_points=total_points,
                passing_score=passing_score,
                created_at=datetime.utcnow(),
                learning_objectives=learning_objectives,
                scoring_rubric=scoring_rubric
            )
            
            # Store assessment
            self.assessments[assessment_id] = assessment
            
            # Convert questions to response format
            question_data = []
            for q in questions:
                question_dict = asdict(q)
                # Remove correct answer from response for security
                if q.question_type == "multiple_choice":
                    question_dict.pop("correct_answer", None)
                question_data.append(question_dict)
            
            return AssessmentResponse(
                success=True,
                assessment_id=assessment_id,
                questions=question_data,
                time_limit=time_limit,
                scoring_rubric=scoring_rubric,
                learning_objectives=learning_objectives
            )
            
        except Exception as e:
            return AssessmentResponse(
                success=False,
                assessment_id="",
                questions=[],
                time_limit=0,
                scoring_rubric={},
                learning_objectives=[]
            )
    
    async def _generate_questions(self, request: AssessmentRequest) -> List[Question]:
        """Generate questions for the assessment"""
        
        questions = []
        
        # Determine question type distribution
        question_types = request.question_types if request.question_types else [
            "multiple_choice", "short_answer", "calculation"
        ]
        
        # Generate questions using AI if available
        if GEMINI_API_KEY:
            ai_questions = await self._generate_ai_questions(request, question_types)
            questions.extend(ai_questions)
        
        # Fill remaining with template questions if needed
        while len(questions) < request.question_count:
            template_question = await self._generate_template_question(
                request.subject, request.topic, request.difficulty_level, question_types
            )
            questions.append(template_question)
        
        return questions[:request.question_count]
    
    async def _generate_ai_questions(self, request: AssessmentRequest, 
                                   question_types: List[str]) -> List[Question]:
        """Generate questions using AI"""
        
        try:
            model = genai.GenerativeModel('gemini-2.5-flash-lite')
            
            prompt = f"""Generate {request.question_count} assessment questions for:

Subject: {request.subject}
Topic: {request.topic}
Difficulty Level: {request.difficulty_level.value}
Question Types: {', '.join(question_types)}

For each question, provide:
1. Question text
2. Question type (from the list above)
3. If multiple choice: 4 options with one correct answer
4. Correct answer or answer key
5. Brief explanation of the correct answer
6. Difficulty level (beginner/intermediate/advanced)
7. Learning objective being tested

Format each question as:
QUESTION [number]:
Type: [question_type]
Text: [question_text]
Options: [if applicable]
Answer: [correct_answer]
Explanation: [explanation]
Difficulty: [difficulty]
Objective: [learning_objective]

Generate questions that are:
- Appropriate for the difficulty level
- Educationally valuable
- Clear and unambiguous
- Properly formatted"""

            response = model.generate_content([prompt])
            
            # Parse AI response into Question objects
            return await self._parse_ai_questions(response.text, request)
            
        except Exception as e:
            print(f"AI question generation error: {e}")
            return []
    
    async def _parse_ai_questions(self, ai_response: str, request: AssessmentRequest) -> List[Question]:
        """Parse AI-generated questions into Question objects"""
        
        questions = []
        lines = ai_response.split('\n')
        
        current_question = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith('QUESTION'):
                # Save previous question if exists
                if current_question:
                    question = await self._create_question_from_dict(current_question, request)
                    if question:
                        questions.append(question)
                
                # Start new question
                current_question = {}
            
            elif ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                
                if key == 'type':
                    current_question['type'] = value
                elif key == 'text':
                    current_question['text'] = value
                elif key == 'options':
                    current_question['options'] = [opt.strip() for opt in value.split(',')]
                elif key == 'answer':
                    current_question['answer'] = value
                elif key == 'explanation':
                    current_question['explanation'] = value
                elif key == 'difficulty':
                    current_question['difficulty'] = value
                elif key == 'objective':
                    current_question['objective'] = value
        
        # Don't forget the last question
        if current_question:
            question = await self._create_question_from_dict(current_question, request)
            if question:
                questions.append(question)
        
        return questions
    
    async def _create_question_from_dict(self, question_data: Dict[str, Any], 
                                       request: AssessmentRequest) -> Optional[Question]:
        """Create Question object from parsed data"""
        
        try:
            # Map difficulty string to enum
            difficulty_map = {
                'beginner': DifficultyLevel.BEGINNER,
                'intermediate': DifficultyLevel.INTERMEDIATE,
                'advanced': DifficultyLevel.ADVANCED,
                'expert': DifficultyLevel.EXPERT
            }
            
            difficulty = difficulty_map.get(
                question_data.get('difficulty', '').lower(), 
                request.difficulty_level
            )
            
            # Determine points based on difficulty and type
            points = 1
            if question_data.get('type') == 'essay':
                points = 5
            elif question_data.get('type') == 'calculation':
                points = 3
            elif difficulty == DifficultyLevel.ADVANCED:
                points = 2
            
            return Question(
                question_id=str(uuid.uuid4()),
                question_text=question_data.get('text', ''),
                question_type=question_data.get('type', 'multiple_choice'),
                options=question_data.get('options'),
                correct_answer=question_data.get('answer'),
                explanation=question_data.get('explanation'),
                points=points,
                difficulty=difficulty,
                topic=request.topic,
                learning_objective=question_data.get('objective')
            )
            
        except Exception as e:
            print(f"Question creation error: {e}")
            return None
    
    async def _generate_template_question(self, subject: str, topic: str, 
                                        difficulty: DifficultyLevel, 
                                        question_types: List[str]) -> Question:
        """Generate a template question when AI is not available"""
        
        question_type = random.choice(question_types)
        
        # Template questions by subject and type
        templates = {
            "mathematics": {
                "multiple_choice": {
                    "text": f"What is the fundamental concept in {topic}?",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "answer": "Option A"
                },
                "calculation": {
                    "text": f"Solve the following {topic} problem: Calculate the result.",
                    "answer": "Show your work and provide the final answer."
                },
                "short_answer": {
                    "text": f"Explain the key principle of {topic} in your own words.",
                    "answer": "A clear explanation of the concept."
                }
            },
            "science": {
                "multiple_choice": {
                    "text": f"Which of the following best describes {topic}?",
                    "options": ["Definition A", "Definition B", "Definition C", "Definition D"],
                    "answer": "Definition A"
                },
                "short_answer": {
                    "text": f"Describe the process involved in {topic}.",
                    "answer": "A detailed description of the process."
                }
            }
        }
        
        # Get template or create generic one
        subject_templates = templates.get(subject.lower(), templates["mathematics"])
        template = subject_templates.get(question_type, subject_templates["multiple_choice"])
        
        return Question(
            question_id=str(uuid.uuid4()),
            question_text=template["text"],
            question_type=question_type,
            options=template.get("options"),
            correct_answer=template["answer"],
            explanation=f"This tests understanding of {topic} concepts.",
            points=1 if difficulty == DifficultyLevel.BEGINNER else 2,
            difficulty=difficulty,
            topic=topic,
            learning_objective=f"Understand {topic} fundamentals"
        )
    
    async def _calculate_time_limit(self, questions: List[Question], 
                                  difficulty: DifficultyLevel) -> int:
        """Calculate appropriate time limit for assessment"""
        
        base_time_per_question = {
            "multiple_choice": 2,
            "true_false": 1,
            "short_answer": 5,
            "essay": 15,
            "calculation": 8
        }
        
        total_minutes = 0
        for question in questions:
            base_time = base_time_per_question.get(question.question_type, 3)
            
            # Adjust for difficulty
            if difficulty == DifficultyLevel.ADVANCED:
                base_time *= 1.5
            elif difficulty == DifficultyLevel.EXPERT:
                base_time *= 2
            
            total_minutes += base_time
        
        # Add buffer time (20%)
        total_minutes = int(total_minutes * 1.2)
        
        # Minimum 10 minutes, maximum 120 minutes
        return max(10, min(total_minutes, 120))
    
    async def _generate_learning_objectives(self, request: AssessmentRequest) -> List[str]:
        """Generate learning objectives for the assessment"""
        
        objectives = [
            f"Demonstrate understanding of {request.topic} concepts",
            f"Apply {request.topic} principles to solve problems",
            f"Analyze {request.topic} scenarios critically"
        ]
        
        if request.difficulty_level in [DifficultyLevel.ADVANCED, DifficultyLevel.EXPERT]:
            objectives.extend([
                f"Evaluate different approaches to {request.topic}",
                f"Synthesize {request.topic} knowledge with other domains"
            ])
        
        return objectives
    
    async def _create_scoring_rubric(self, questions: List[Question], 
                                   difficulty: DifficultyLevel) -> Dict[str, Any]:
        """Create scoring rubric for the assessment"""
        
        total_points = sum(q.points for q in questions)
        
        rubric = {
            "total_points": total_points,
            "grading_scale": {
                "A": {"min_percentage": 90, "description": "Excellent understanding"},
                "B": {"min_percentage": 80, "description": "Good understanding"},
                "C": {"min_percentage": 70, "description": "Satisfactory understanding"},
                "D": {"min_percentage": 60, "description": "Basic understanding"},
                "F": {"min_percentage": 0, "description": "Insufficient understanding"}
            },
            "question_types": {},
            "feedback_criteria": {
                "excellent": "Demonstrates mastery of all concepts",
                "good": "Shows solid understanding with minor gaps",
                "satisfactory": "Meets basic requirements",
                "needs_improvement": "Requires additional study and practice"
            }
        }
        
        # Add question type breakdown
        for question in questions:
            q_type = question.question_type
            if q_type not in rubric["question_types"]:
                rubric["question_types"][q_type] = {
                    "count": 0,
                    "total_points": 0
                }
            
            rubric["question_types"][q_type]["count"] += 1
            rubric["question_types"][q_type]["total_points"] += question.points
        
        return rubric
    
    async def submit_assessment(self, assessment_id: str, user_id: str, 
                              answers: Dict[str, Any]) -> Dict[str, Any]:
        """Submit and grade an assessment"""
        
        try:
            assessment = self.assessments.get(assessment_id)
            if not assessment:
                return {"success": False, "error": "Assessment not found"}
            
            # Grade the assessment
            results = await self._grade_assessment(assessment, answers)
            
            # Store results
            result_id = str(uuid.uuid4())
            self.assessment_results[result_id] = {
                "result_id": result_id,
                "assessment_id": assessment_id,
                "user_id": user_id,
                "submitted_at": datetime.utcnow().isoformat(),
                "answers": answers,
                "results": results
            }
            
            return {
                "success": True,
                "result_id": result_id,
                "score": results["score"],
                "percentage": results["percentage"],
                "grade": results["grade"],
                "feedback": results["feedback"],
                "detailed_results": results["question_results"]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _grade_assessment(self, assessment: Assessment, 
                              answers: Dict[str, Any]) -> Dict[str, Any]:
        """Grade an assessment submission"""
        
        total_points = 0
        earned_points = 0
        question_results = []
        
        for question in assessment.questions:
            question_id = question.question_id
            user_answer = answers.get(question_id, "")
            
            # Grade based on question type
            points_earned = 0
            is_correct = False
            feedback = ""
            
            if question.question_type == "multiple_choice":
                if user_answer == question.correct_answer:
                    points_earned = question.points
                    is_correct = True
                    feedback = "Correct!"
                else:
                    feedback = f"Incorrect. The correct answer is: {question.correct_answer}"
            
            elif question.question_type == "true_false":
                if user_answer.lower() == question.correct_answer.lower():
                    points_earned = question.points
                    is_correct = True
                    feedback = "Correct!"
                else:
                    feedback = f"Incorrect. The correct answer is: {question.correct_answer}"
            
            elif question.question_type in ["short_answer", "essay"]:
                # For open-ended questions, give partial credit based on keywords
                points_earned = await self._grade_open_ended(
                    user_answer, question.correct_answer, question.points
                )
                is_correct = points_earned > 0
                feedback = "Graded based on content and understanding."
            
            elif question.question_type == "calculation":
                # For calculations, check if the answer is numerically close
                points_earned = await self._grade_calculation(
                    user_answer, question.correct_answer, question.points
                )
                is_correct = points_earned > 0
                feedback = "Graded based on correctness of calculation."
            
            # Add explanation if available
            if question.explanation and not is_correct:
                feedback += f" Explanation: {question.explanation}"
            
            question_results.append({
                "question_id": question_id,
                "question_text": question.question_text,
                "user_answer": user_answer,
                "correct_answer": question.correct_answer,
                "points_possible": question.points,
                "points_earned": points_earned,
                "is_correct": is_correct,
                "feedback": feedback
            })
            
            total_points += question.points
            earned_points += points_earned
        
        # Calculate final grade
        percentage = (earned_points / total_points) * 100 if total_points > 0 else 0
        grade = await self._calculate_letter_grade(percentage, assessment.scoring_rubric)
        
        # Generate overall feedback
        overall_feedback = await self._generate_overall_feedback(
            percentage, assessment.difficulty_level, question_results
        )
        
        return {
            "score": earned_points,
            "total_possible": total_points,
            "percentage": percentage,
            "grade": grade,
            "feedback": overall_feedback,
            "question_results": question_results
        }
    
    async def _grade_open_ended(self, user_answer: str, correct_answer: str, 
                              max_points: int) -> int:
        """Grade open-ended questions based on content"""
        
        if not user_answer.strip():
            return 0
        
        # Simple keyword matching (in production, use more sophisticated NLP)
        user_words = set(user_answer.lower().split())
        correct_words = set(correct_answer.lower().split())
        
        # Calculate overlap
        overlap = len(user_words.intersection(correct_words))
        total_keywords = len(correct_words)
        
        if total_keywords == 0:
            return max_points // 2  # Give partial credit if no reference answer
        
        # Award points based on keyword overlap
        overlap_ratio = overlap / total_keywords
        
        if overlap_ratio >= 0.8:
            return max_points
        elif overlap_ratio >= 0.6:
            return int(max_points * 0.8)
        elif overlap_ratio >= 0.4:
            return int(max_points * 0.6)
        elif overlap_ratio >= 0.2:
            return int(max_points * 0.4)
        else:
            return 0
    
    async def _grade_calculation(self, user_answer: str, correct_answer: str, 
                               max_points: int) -> int:
        """Grade calculation questions"""
        
        try:
            # Extract numbers from answers
            import re
            
            user_numbers = re.findall(r'-?\d+\.?\d*', user_answer)
            correct_numbers = re.findall(r'-?\d+\.?\d*', correct_answer)
            
            if not user_numbers or not correct_numbers:
                return 0
            
            # Compare the main numerical result (usually the last number)
            user_result = float(user_numbers[-1])
            correct_result = float(correct_numbers[-1])
            
            # Allow for small rounding errors
            tolerance = abs(correct_result) * 0.01  # 1% tolerance
            
            if abs(user_result - correct_result) <= tolerance:
                return max_points
            elif abs(user_result - correct_result) <= tolerance * 5:  # 5% tolerance
                return int(max_points * 0.8)  # Partial credit
            else:
                return 0
                
        except (ValueError, IndexError):
            return 0
    
    async def _calculate_letter_grade(self, percentage: float, 
                                    rubric: Dict[str, Any]) -> str:
        """Calculate letter grade based on percentage and rubric"""
        
        grading_scale = rubric.get("grading_scale", {})
        
        for grade, criteria in grading_scale.items():
            if percentage >= criteria["min_percentage"]:
                return grade
        
        return "F"
    
    async def _generate_overall_feedback(self, percentage: float, 
                                       difficulty: DifficultyLevel,
                                       question_results: List[Dict]) -> str:
        """Generate overall feedback for the assessment"""
        
        feedback_parts = []
        
        # Performance feedback
        if percentage >= 90:
            feedback_parts.append("Excellent work! You demonstrate mastery of the concepts.")
        elif percentage >= 80:
            feedback_parts.append("Good job! You show solid understanding of the material.")
        elif percentage >= 70:
            feedback_parts.append("Satisfactory performance. You meet the basic requirements.")
        elif percentage >= 60:
            feedback_parts.append("You show basic understanding but need more practice.")
        else:
            feedback_parts.append("Additional study and practice are needed to master these concepts.")
        
        # Analyze performance by question type
        correct_by_type = {}
        total_by_type = {}
        
        for result in question_results:
            q_type = "general"  # Simplified for template
            if q_type not in correct_by_type:
                correct_by_type[q_type] = 0
                total_by_type[q_type] = 0
            
            if result["is_correct"]:
                correct_by_type[q_type] += 1
            total_by_type[q_type] += 1
        
        # Provide specific feedback
        weak_areas = []
        strong_areas = []
        
        for q_type, correct_count in correct_by_type.items():
            total_count = total_by_type[q_type]
            success_rate = correct_count / total_count if total_count > 0 else 0
            
            if success_rate < 0.6:
                weak_areas.append(q_type)
            elif success_rate > 0.8:
                strong_areas.append(q_type)
        
        if strong_areas:
            feedback_parts.append(f"Strengths: {', '.join(strong_areas)}")
        
        if weak_areas:
            feedback_parts.append(f"Areas for improvement: {', '.join(weak_areas)}")
        
        # Difficulty-specific feedback
        if difficulty == DifficultyLevel.ADVANCED and percentage >= 70:
            feedback_parts.append("Great job tackling advanced concepts!")
        elif difficulty == DifficultyLevel.BEGINNER and percentage < 70:
            feedback_parts.append("Focus on mastering the fundamentals before moving to more complex topics.")
        
        return " ".join(feedback_parts)
    
    async def get_assessment(self, assessment_id: str) -> Optional[Assessment]:
        """Retrieve an assessment by ID"""
        return self.assessments.get(assessment_id)
    
    async def get_assessment_results(self, result_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve assessment results by ID"""
        return self.assessment_results.get(result_id)


class ContentGenerationService:
    """Service for generating educational content"""
    
    def __init__(self):
        self.generated_content = {}
    
    async def generate_content(self, request: ContentGenerationRequest) -> ContentGenerationResponse:
        """Generate educational content based on request"""
        
        try:
            content_id = str(uuid.uuid4())
            
            # Generate main content
            content = await self._generate_main_content(request)
            
            # Generate title
            title = await self._generate_title(request, content)
            
            # Create metadata
            metadata = await self._create_content_metadata(request, content)
            
            # Generate interactive elements
            interactive_elements = await self._generate_interactive_elements(request, content)
            
            # Generate assessment questions
            assessment_questions = await self._generate_assessment_questions(request, content)
            
            # Store generated content
            generated_content = {
                "content_id": content_id,
                "title": title,
                "content": content,
                "metadata": metadata,
                "interactive_elements": interactive_elements,
                "assessment_questions": assessment_questions,
                "created_at": datetime.utcnow().isoformat(),
                "request_params": asdict(request) if hasattr(request, '__dict__') else vars(request)
            }
            
            self.generated_content[content_id] = generated_content
            
            return ContentGenerationResponse(
                success=True,
                content_id=content_id,
                title=title,
                content=content,
                metadata=metadata,
                interactive_elements=interactive_elements,
                assessment_questions=assessment_questions
            )
            
        except Exception as e:
            return ContentGenerationResponse(
                success=False,
                content_id="",
                title="Content Generation Failed",
                content=f"Failed to generate content: {str(e)}",
                metadata={},
                interactive_elements=[],
                assessment_questions=[]
            )
    
    async def _generate_main_content(self, request: ContentGenerationRequest) -> str:
        """Generate the main educational content"""
        
        if not GEMINI_API_KEY:
            return await self._generate_template_content(request)
        
        try:
            model = genai.GenerativeModel('gemini-2.5-flash-lite')
            
            prompt = f"""Create comprehensive educational content for:

Topic: {request.topic}
Content Type: {request.content_type}
Difficulty Level: {request.difficulty_level.value}
Duration: {request.duration_minutes} minutes
Learning Objectives: {', '.join(request.learning_objectives)}
Format Preferences: {', '.join(request.format_preferences) if request.format_preferences else 'Standard format'}

Requirements:
1. Create engaging, educational content appropriate for the difficulty level
2. Structure the content clearly with headings and sections
3. Include examples and practical applications
4. Use markdown formatting for better readability
5. Ensure content can be completed in the specified duration
6. Address all learning objectives
7. Include key concepts, definitions, and explanations
8. Add practice exercises or activities where appropriate

Content Type Guidelines:
- Lesson: Structured learning material with explanations and examples
- Quiz: Questions and answers with explanations
- Exercise: Hands-on activities and practice problems
- Tutorial: Step-by-step instructions and guidance
- Reference: Comprehensive information and definitions

Generate high-quality educational content that engages learners and facilitates understanding."""

            response = model.generate_content([prompt])
            return response.text
            
        except Exception as e:
            print(f"Content generation error: {e}")
            return await self._generate_template_content(request)
    
    async def _generate_template_content(self, request: ContentGenerationRequest) -> str:
        """Generate template content when AI is not available"""
        
        content_templates = {
            "lesson": f"""# {request.topic}

## Introduction
Welcome to this lesson on {request.topic}. In this {request.duration_minutes}-minute session, you will learn the fundamental concepts and practical applications.

## Learning Objectives
By the end of this lesson, you will be able to:
{chr(10).join(f"- {obj}" for obj in request.learning_objectives)}

## Key Concepts

### Concept 1: Fundamentals
Understanding the basic principles of {request.topic} is essential for building a strong foundation.

### Concept 2: Applications
Learn how {request.topic} is applied in real-world scenarios and practical situations.

### Concept 3: Advanced Topics
Explore more complex aspects of {request.topic} for deeper understanding.

## Examples
Here are some practical examples to illustrate the concepts:

1. **Example 1**: Basic application of {request.topic}
2. **Example 2**: Intermediate use case
3. **Example 3**: Advanced implementation

## Practice Activities
1. Complete the guided exercises
2. Apply concepts to new scenarios
3. Reflect on learning and ask questions

## Summary
In this lesson, we covered the essential aspects of {request.topic}. Continue practicing to reinforce your understanding.

## Next Steps
- Review the key concepts
- Complete additional practice exercises
- Explore related topics for deeper learning
""",
            
            "quiz": f"""# {request.topic} Quiz

## Instructions
This quiz covers the key concepts of {request.topic}. Take your time and think carefully about each question.

## Questions

### Question 1: Multiple Choice
What is the most important aspect of {request.topic}?
a) Option A
b) Option B
c) Option C
d) Option D

**Answer**: Option A
**Explanation**: This is the correct answer because...

### Question 2: Short Answer
Explain the main principle of {request.topic} in your own words.

**Sample Answer**: The main principle involves...

### Question 3: Application
How would you apply {request.topic} in a real-world scenario?

**Sample Answer**: In practice, you would...

## Answer Key
1. A - Explanation provided above
2. Open-ended - Look for key concepts in the answer
3. Open-ended - Evaluate practical understanding

## Scoring
- 3 correct: Excellent understanding
- 2 correct: Good grasp of concepts
- 1 correct: Review material and try again
- 0 correct: Additional study needed
""",
            
            "exercise": f"""# {request.topic} Exercises

## Overview
These hands-on exercises will help you practice and apply {request.topic} concepts.

## Exercise 1: Basic Practice
**Objective**: Apply fundamental concepts of {request.topic}

**Instructions**:
1. Review the basic principles
2. Follow the step-by-step process
3. Complete the practice problems
4. Check your answers

**Materials Needed**:
- Notebook and pen
- Calculator (if applicable)
- Reference materials

## Exercise 2: Intermediate Challenge
**Objective**: Solve more complex problems using {request.topic}

**Instructions**:
1. Analyze the given scenario
2. Identify the relevant concepts
3. Apply appropriate methods
4. Verify your solution

## Exercise 3: Advanced Application
**Objective**: Create original solutions using {request.topic}

**Instructions**:
1. Design your own problem
2. Solve it using learned concepts
3. Explain your reasoning
4. Share with others for feedback

## Reflection Questions
1. What did you learn from these exercises?
2. Which concepts were most challenging?
3. How can you apply this knowledge in other contexts?
4. What questions do you still have?

## Additional Resources
- Reference materials for further study
- Online tools and calculators
- Practice problem sets
- Community forums for discussion
"""
        }
        
        template = content_templates.get(request.content_type.lower(), content_templates["lesson"])
        return template
    
    async def _generate_title(self, request: ContentGenerationRequest, content: str) -> str:
        """Generate an appropriate title for the content"""
        
        # Extract title from content if it has one
        lines = content.split('\n')
        for line in lines:
            if line.startswith('# '):
                return line[2:].strip()
        
        # Generate title based on request
        type_titles = {
            "lesson": f"{request.topic} - Complete Lesson",
            "quiz": f"{request.topic} - Assessment Quiz",
            "exercise": f"{request.topic} - Practice Exercises",
            "tutorial": f"{request.topic} - Step-by-Step Tutorial",
            "reference": f"{request.topic} - Reference Guide"
        }
        
        return type_titles.get(request.content_type.lower(), f"{request.topic} - Educational Content")
    
    async def _create_content_metadata(self, request: ContentGenerationRequest, 
                                     content: str) -> Dict[str, Any]:
        """Create metadata for the generated content"""
        
        word_count = len(content.split())
        estimated_reading_time = max(1, word_count // 200)  # Assume 200 words per minute
        
        return {
            "topic": request.topic,
            "content_type": request.content_type,
            "difficulty_level": request.difficulty_level.value,
            "target_duration_minutes": request.duration_minutes,
            "estimated_reading_time_minutes": estimated_reading_time,
            "word_count": word_count,
            "learning_objectives": request.learning_objectives,
            "format_preferences": request.format_preferences,
            "created_at": datetime.utcnow().isoformat(),
            "content_structure": await self._analyze_content_structure(content),
            "key_topics": await self._extract_key_topics(content),
            "complexity_score": await self._calculate_complexity_score(content, request.difficulty_level)
        }
    
    async def _generate_interactive_elements(self, request: ContentGenerationRequest, 
                                           content: str) -> List[Dict[str, Any]]:
        """Generate interactive elements for the content"""
        
        elements = []
        
        # Add interactive elements based on content type
        if request.content_type.lower() == "lesson":
            elements.extend([
                {
                    "type": "knowledge_check",
                    "title": "Quick Knowledge Check",
                    "description": "Test your understanding of key concepts",
                    "config": {
                        "questions": 3,
                        "format": "multiple_choice",
                        "immediate_feedback": True
                    }
                },
                {
                    "type": "interactive_diagram",
                    "title": f"{request.topic} Visualization",
                    "description": "Interactive diagram to explore concepts",
                    "config": {
                        "type": "concept_map",
                        "interactive": True,
                        "annotations": True
                    }
                }
            ])
        
        elif request.content_type.lower() == "exercise":
            elements.extend([
                {
                    "type": "practice_simulator",
                    "title": "Practice Simulator",
                    "description": "Hands-on practice environment",
                    "config": {
                        "guided_mode": True,
                        "hints_available": True,
                        "progress_tracking": True
                    }
                },
                {
                    "type": "peer_collaboration",
                    "title": "Collaborative Exercise",
                    "description": "Work with others on practice problems",
                    "config": {
                        "max_participants": 4,
                        "shared_workspace": True,
                        "real_time_sync": True
                    }
                }
            ])
        
        # Add common interactive elements
        elements.append({
            "type": "progress_tracker",
            "title": "Learning Progress",
            "description": "Track your progress through the content",
            "config": {
                "milestones": await self._extract_milestones(content),
                "completion_criteria": "all_sections_viewed",
                "badges_enabled": True
            }
        })
        
        return elements
    
    async def _generate_assessment_questions(self, request: ContentGenerationRequest, 
                                           content: str) -> List[Dict[str, Any]]:
        """Generate assessment questions based on the content"""
        
        questions = []
        
        # Generate questions based on learning objectives
        for i, objective in enumerate(request.learning_objectives[:5]):  # Limit to 5 questions
            question = {
                "question_id": str(uuid.uuid4()),
                "question_text": f"How well do you understand: {objective}?",
                "question_type": "self_assessment",
                "scale": {
                    "min": 1,
                    "max": 5,
                    "labels": {
                        "1": "Not at all",
                        "2": "Slightly",
                        "3": "Moderately", 
                        "4": "Well",
                        "5": "Very well"
                    }
                },
                "learning_objective": objective
            }
            questions.append(question)
        
        # Add content-specific questions
        if "example" in content.lower():
            questions.append({
                "question_id": str(uuid.uuid4()),
                "question_text": f"Can you think of another example of {request.topic} in real life?",
                "question_type": "open_ended",
                "expected_length": "short",
                "learning_objective": "Apply concepts to new situations"
            })
        
        if request.content_type.lower() in ["lesson", "tutorial"]:
            questions.append({
                "question_id": str(uuid.uuid4()),
                "question_text": f"What is the most important thing you learned about {request.topic}?",
                "question_type": "reflection",
                "expected_length": "medium",
                "learning_objective": "Reflect on key learnings"
            })
        
        return questions
    
    # Helper methods for content analysis
    async def _analyze_content_structure(self, content: str) -> Dict[str, Any]:
        """Analyze the structure of the generated content"""
        
        lines = content.split('\n')
        structure = {
            "sections": 0,
            "subsections": 0,
            "paragraphs": 0,
            "lists": 0,
            "code_blocks": 0,
            "has_introduction": False,
            "has_conclusion": False
        }
        
        for line in lines:
            line = line.strip()
            if line.startswith('# '):
                structure["sections"] += 1
            elif line.startswith('## '):
                structure["subsections"] += 1
            elif line.startswith(('- ', '* ', '1.', '2.', '3.')):
                structure["lists"] += 1
            elif line.startswith('```'):
                structure["code_blocks"] += 1
            elif 'introduction' in line.lower():
                structure["has_introduction"] = True
            elif any(word in line.lower() for word in ['conclusion', 'summary', 'wrap up']):
                structure["has_conclusion"] = True
        
        # Count paragraphs (non-empty lines that aren't headers or lists)
        for line in lines:
            line = line.strip()
            if (line and 
                not line.startswith('#') and 
                not line.startswith(('- ', '* ', '1.', '2.', '3.')) and
                not line.startswith('```')):
                structure["paragraphs"] += 1
        
        return structure
    
    async def _extract_key_topics(self, content: str) -> List[str]:
        """Extract key topics from the content"""
        
        # Simple keyword extraction (in production, use more sophisticated NLP)
        topics = []
        lines = content.split('\n')
        
        for line in lines:
            if line.startswith('##'):  # Subsection headers often contain key topics
                topic = line.replace('#', '').strip()
                if len(topic) > 3 and len(topic) < 50:
                    topics.append(topic)
        
        return topics[:10]  # Limit to 10 key topics
    
    async def _calculate_complexity_score(self, content: str, 
                                        difficulty: DifficultyLevel) -> float:
        """Calculate a complexity score for the content"""
        
        # Simple complexity calculation based on various factors
        score = 0.0
        
        # Base score from difficulty level
        difficulty_scores = {
            DifficultyLevel.BEGINNER: 0.2,
            DifficultyLevel.INTERMEDIATE: 0.5,
            DifficultyLevel.ADVANCED: 0.8,
            DifficultyLevel.EXPERT: 1.0
        }
        score += difficulty_scores.get(difficulty, 0.5)
        
        # Adjust based on content characteristics
        word_count = len(content.split())
        if word_count > 1000:
            score += 0.1
        if word_count > 2000:
            score += 0.1
        
        # Technical terms increase complexity
        technical_indicators = ['algorithm', 'formula', 'equation', 'theorem', 'principle']
        technical_count = sum(1 for term in technical_indicators if term in content.lower())
        score += technical_count * 0.05
        
        # Mathematical notation increases complexity
        if any(char in content for char in ['∑', '∫', '∂', '≈', '≤', '≥']):
            score += 0.1
        
        return min(score, 1.0)  # Cap at 1.0
    
    async def _extract_milestones(self, content: str) -> List[str]:
        """Extract learning milestones from content"""
        
        milestones = []
        lines = content.split('\n')
        
        for line in lines:
            if line.startswith('## '):  # Section headers as milestones
                milestone = line[3:].strip()
                if milestone and len(milestone) < 100:
                    milestones.append(milestone)
        
        return milestones[:8]  # Limit to 8 milestones
    
    async def get_generated_content(self, content_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve generated content by ID"""
        return self.generated_content.get(content_id)


# Service instances
assessment_service = AssessmentService()
content_generation_service = ContentGenerationService()