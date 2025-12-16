"""AI Tutoring service for enhanced feedback and study planning"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import json
import re
import google.generativeai as genai
from supabase import Client
from app.config import settings
from app.models.base import Subject
from app.utils.exceptions import APIException
from app.services.wolfram_service import WolframService

# Configure Gemini
genai.configure(api_key=settings.gemini_api_key)


class AITutoringService:
    """Service for AI-powered tutoring, feedback, and study planning"""
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        # Use gemini-2.5-flash (fastest and most capable) or fallback to older models
        try:
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        except:
            try:
                self.model = genai.GenerativeModel('gemini-1.5-flash')
            except:
                self.model = genai.GenerativeModel('gemini-pro')
        self.wolfram_service = WolframService()
    
    async def get_personalized_feedback(
        self,
        user_id: str,
        content: str,
        subject: Subject,
        performance_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate personalized feedback based on student performance
        
        Args:
            user_id: Student user ID
            content: Content/question/answer to provide feedback on
            subject: Subject area
            performance_data: Optional performance metrics
        
        Returns:
            Dictionary with feedback, suggestions, and improvement areas
        """
        try:
            # Get student progress if not provided
            if not performance_data:
                progress_response = self.supabase.table('progress').select('*').eq('user_id', user_id).eq('subject', subject.value).execute()
                performance_data = {
                    'mastery_scores': [p.get('mastery_score', 0) for p in progress_response.data],
                    'streak_days': progress_response.data[0].get('streak_days', 0) if progress_response.data else 0
                }
            
            prompt = f"""You are an AI tutor helping a Class 12 student with {subject.value}.

Student's current performance:
- Average mastery score: {sum(performance_data.get('mastery_scores', [0])) / max(len(performance_data.get('mastery_scores', [1])), 1):.1f}%
- Current streak: {performance_data.get('streak_days', 0)} days

Student's work:
{content}

Provide:
1. Specific, constructive feedback on what they did well
2. Areas for improvement with actionable suggestions
3. Encouragement and motivation
4. Next steps to strengthen understanding

Format your response as JSON with keys: feedback, strengths, improvements, next_steps, encouragement"""

            response = self.model.generate_content(prompt)
            feedback_text = response.text
            
            # Parse JSON response (simple extraction)
            json_match = re.search(r'\{.*\}', feedback_text, re.DOTALL)
            if json_match:
                feedback_data = json.loads(json_match.group())
            else:
                # Fallback if JSON parsing fails
                feedback_data = {
                    'feedback': feedback_text,
                    'strengths': [],
                    'improvements': [],
                    'next_steps': [],
                    'encouragement': feedback_text
                }
            
            return {
                'user_id': user_id,
                'subject': subject.value,
                'feedback': feedback_data,
                'generated_at': datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise APIException(
                code="FEEDBACK_GENERATION_ERROR",
                message=f"Failed to generate feedback: {str(e)}",
                status_code=500
            )
    
    async def generate_study_plan(
        self,
        user_id: str,
        subject: Subject,
        days: int = 7,
        hours_per_day: float = 2.0
    ) -> Dict[str, Any]:
        """
        Generate personalized study plan
        
        Args:
            user_id: Student user ID
            subject: Subject to create plan for
            days: Number of days for the plan
            hours_per_day: Hours available per day
        
        Returns:
            Detailed study plan with topics, activities, and timeline
        """
        try:
            # Get student progress
            progress_response = self.supabase.table('progress').select('*, topics(*)').eq('user_id', user_id).eq('subject', subject.value).execute()
            
            # Get weak areas (low mastery scores)
            weak_topics = [
                p for p in progress_response.data 
                if p.get('mastery_score', 0) < 60
            ]
            
            # Get upcoming topics
            topics_response = self.supabase.table('topics').select('*').eq('subject', subject.value).order('order_index').execute()
            all_topics = topics_response.data
            
            prompt = f"""Create a personalized {days}-day study plan for a Class 12 {subject.value} student.

Available time: {hours_per_day} hours per day
Total days: {days}

Student's weak areas (need more practice):
{json.dumps([{'topic': t.get('topics', {}).get('name', 'Unknown'), 'mastery': t.get('mastery_score', 0)} for t in weak_topics[:5]], indent=2) if weak_topics else 'None identified'}

All topics to cover:
{json.dumps([{'name': t.get('name'), 'chapter': t.get('chapter')} for t in all_topics[:10]], indent=2)}

Create a detailed study plan with:
1. Daily schedule with specific topics
2. Learning activities (reading, practice problems, videos)
3. Practice goals for each day
4. Review sessions for weak areas
5. Assessment checkpoints

Format as JSON with structure:
{{
  "plan_duration_days": {days},
  "daily_schedule": [
    {{
      "day": 1,
      "date": "YYYY-MM-DD",
      "topics": ["topic1", "topic2"],
      "activities": [
        {{"type": "reading", "duration_minutes": 30, "description": "..."}},
        {{"type": "practice", "duration_minutes": 45, "description": "..."}}
      ],
      "goals": ["goal1", "goal2"],
      "review_topics": ["weak_topic1"]
    }}
  ],
  "assessment_checkpoints": [
    {{"day": 3, "type": "quiz", "topics": ["topic1", "topic2"]}}
  ],
  "total_hours": {days * hours_per_day}
}}"""

            response = self.model.generate_content(prompt)
            plan_text = response.text
            
            # Parse JSON response
            json_match = re.search(r'\{.*\}', plan_text, re.DOTALL)
            if json_match:
                plan_data = json.loads(json_match.group())
            else:
                raise APIException(
                    code="PLAN_PARSING_ERROR",
                    message="Failed to parse study plan response",
                    status_code=500
                )
            
            return {
                'user_id': user_id,
                'subject': subject.value,
                'plan': plan_data,
                'generated_at': datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise APIException(
                code="STUDY_PLAN_ERROR",
                message=f"Failed to generate study plan: {str(e)}",
                status_code=500
            )
    
    async def answer_question(
        self,
        user_id: str,
        question: str,
        subject: Subject,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Answer student questions with explanations using Gemini + Wolfram Alpha
        
        Args:
            user_id: Student user ID
            question: Student's question
            subject: Subject area
            context: Optional context or previous conversation
        
        Returns:
            Answer with explanation and related resources
        """
        try:
            # Check if it's a mathematical/numerical question or requests a graph
            is_math_question = self.wolfram_service.is_numerical_question(question)
            requests_graph = any(keyword in question.lower() for keyword in ['plot', 'graph', 'visualize', 'draw', 'show'])
            wolfram_result = None
            
            # Use Wolfram Alpha for mathematical questions or graph requests
            if (is_math_question or requests_graph) and subject.value in ['mathematics', 'physics', 'chemistry']:
                try:
                    # For graph requests, include the request in the query
                    wolfram_query = question
                    if requests_graph and 'plot' not in question.lower() and 'graph' not in question.lower():
                        wolfram_query = f"plot {question}"
                    
                    wolfram_result = await self.wolfram_service.solve_math_problem(
                        wolfram_query,
                        include_steps=True
                    )
                except Exception as e:
                    print(f"Wolfram Alpha error: {e}")
                    # Continue with Gemini if Wolfram fails
            
            # Build enhanced prompt with Wolfram results if available
            wolfram_context = ""
            if wolfram_result:
                wolfram_context = f"""
Wolfram Alpha Solution:
- Answer: {wolfram_result.get('answer', 'N/A')}
- Input Interpretation: {wolfram_result.get('input_interpretation', 'N/A')}
- Steps: {json.dumps(wolfram_result.get('steps', []), indent=2)}
"""
            
            prompt = f"""You are an expert AI tutor helping a Class 12 student with {subject.value}. Your goal is to TEACH, not just answer. Make learning engaging and comprehensive.

Student's question: {question}

{f"Context from previous conversation: {context}" if context else ""}

{wolfram_context if wolfram_result else ""}

Provide a comprehensive, educational response that:
1. **Answer**: Give a clear, step-by-step answer (use Wolfram results if provided, but explain them pedagogically)
2. **Explanation**: Break down WHY the answer works, not just WHAT the answer is. Explain the underlying concepts, principles, and reasoning
3. **Teaching Approach**: Use the Socratic method - guide the student to understand, don't just give answers
4. **Examples**: Provide 2-3 real-world examples or analogies that make the concept relatable
5. **Step-by-Step Breakdown**: If it's a problem-solving question, show each step with clear reasoning
6. **Practice Suggestions**: Suggest 2-3 practice problems or exercises to reinforce learning
7. **Common Mistakes**: Warn about 2-3 common mistakes students make with this concept
8. **Connections**: Connect this concept to related topics they've learned or will learn
9. **Visual Aids**: Suggest diagrams, graphs, or visualizations that would help (describe them)

Be encouraging, patient, and adapt your explanation to a Class 12 level. Use analogies and examples that resonate with teenagers.

Format as JSON with keys: answer, explanation, examples, step_by_step, practice_suggestions, common_mistakes, connections, visual_aids, teaching_tips"""

            try:
                response = self.model.generate_content(prompt)
                answer_text = response.text
            except Exception as gemini_error:
                error_msg = str(gemini_error)
                print(f"Gemini API error: {error_msg}")  # Debug logging
                if "API key" in error_msg or "API_KEY" in error_msg or "expired" in error_msg.lower():
                    raise APIException(
                        code="GEMINI_API_KEY_ERROR",
                        message="Gemini API key is invalid or expired. Please check your GEMINI_API_KEY in .env file.",
                        status_code=500
                    )
                # Re-raise with more context
                raise APIException(
                    code="GEMINI_GENERATION_ERROR",
                    message=f"Failed to generate response: {error_msg}",
                    status_code=500
                )
            
            # Parse JSON response
            try:
                json_match = re.search(r'\{.*\}', answer_text, re.DOTALL)
                if json_match:
                    answer_data = json.loads(json_match.group())
                else:
                    # Fallback if JSON parsing fails
                    print(f"Warning: Could not find JSON in Gemini response. Raw response: {answer_text[:200]}")
                    answer_data = {
                        'answer': answer_text,
                        'explanation': answer_text,
                        'examples': [],
                        'step_by_step': [],
                        'practice_suggestions': [],
                        'common_mistakes': [],
                        'connections': [],
                        'visual_aids': [],
                        'teaching_tips': []
                    }
            except json.JSONDecodeError as json_error:
                print(f"JSON parsing error: {json_error}. Response text: {answer_text[:500]}")
                # Fallback if JSON parsing fails
                answer_data = {
                    'answer': answer_text,
                    'explanation': answer_text,
                    'examples': [],
                    'step_by_step': [],
                    'practice_suggestions': [],
                    'common_mistakes': [],
                    'connections': [],
                    'visual_aids': [],
                    'teaching_tips': []
                }
            
            # Enhance with Wolfram data if available
            if wolfram_result:
                # Add Wolfram steps to step_by_step
                if not answer_data.get('step_by_step'):
                    answer_data['step_by_step'] = []
                
                # Add Wolfram steps
                for idx, step in enumerate(wolfram_result.get('steps', []), 1):
                    answer_data['step_by_step'].append({
                        'step_number': idx,
                        'description': step.get('title', f'Step {idx}'),
                        'content': step.get('content', ''),
                        'source': 'wolfram'
                    })
                
                # Add Wolfram answer if not already included
                if wolfram_result.get('answer') and not answer_data.get('answer'):
                    answer_data['answer'] = f"According to Wolfram Alpha: {wolfram_result['answer']}"
                
                # Add plots/graphs if available
                plots = wolfram_result.get('plots')
                if plots and isinstance(plots, list) and len(plots) > 0:
                    if not answer_data.get('visual_aids'):
                        answer_data['visual_aids'] = []
                    for plot in plots:
                        if isinstance(plot, dict) and plot.get('url'):
                            answer_data['visual_aids'].append({
                                'type': 'plot',
                                'title': plot.get('title', 'Graph'),
                                'description': plot.get('title', 'Visualization from Wolfram Alpha'),
                                'url': plot.get('url'),
                                'source': 'wolfram'
                            })
            
            return {
                'user_id': user_id,
                'question': question,
                'subject': subject.value,
                'answer': answer_data,
                'wolfram_used': wolfram_result is not None,
                'timestamp': datetime.utcnow().isoformat()
            }
        except APIException:
            # Re-raise API exceptions as-is
            raise
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Unexpected error in answer_question: {str(e)}")
            print(f"Traceback: {error_trace}")
            raise APIException(
                code="QUESTION_ANSWER_ERROR",
                message=f"Failed to answer question: {str(e)}",
                status_code=500
            )

