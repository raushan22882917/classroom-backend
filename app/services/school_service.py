"""School management service for admin operations"""

from typing import Optional, List, Dict
from datetime import datetime
from supabase import create_client, Client
import httpx

from app.config import settings
from app.utils.exceptions import APIException


class SchoolService:
    """Service for school management operations"""
    
    def __init__(self):
        """Initialize school service with Supabase client"""
        self.supabase: Client = create_client(
            settings.supabase_url,
            settings.supabase_service_key  # Use service key for admin operations
        )
    
    async def create_school(
        self,
        name: str,
        address: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        pincode: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        principal_name: Optional[str] = None
    ) -> Dict:
        """Create a new school"""
        try:
            school_data = {
                "name": name,
                "address": address,
                "city": city,
                "state": state,
                "pincode": pincode,
                "phone": phone,
                "email": email,
                "principal_name": principal_name,
                "is_active": True
            }
            
            response = self.supabase.table("schools").insert(school_data).execute()
            
            if not response.data:
                raise APIException("Failed to create school", 500)
            
            return response.data[0]
            
        except Exception as e:
            if isinstance(e, APIException):
                raise
            raise APIException(f"Error creating school: {str(e)}", 500)
    
    async def get_schools(
        self,
        city: Optional[str] = None,
        state: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """Get list of schools with optional filters"""
        try:
            query = self.supabase.table("schools").select("*")
            
            if city:
                query = query.eq("city", city)
            if state:
                query = query.eq("state", state)
            if is_active is not None:
                query = query.eq("is_active", is_active)
            
            query = query.order("name").limit(limit).offset(offset)
            response = query.execute()
            
            return response.data or []
            
        except Exception as e:
            raise APIException(f"Error fetching schools: {str(e)}", 500)
    
    async def get_school(self, school_id: str) -> Dict:
        """Get a specific school by ID"""
        try:
            response = self.supabase.table("schools").select("*").eq("id", school_id).execute()
            
            if not response.data:
                raise APIException("School not found", 404)
            
            return response.data[0]
            
        except Exception as e:
            if isinstance(e, APIException):
                raise
            raise APIException(f"Error fetching school: {str(e)}", 500)
    
    async def update_school(
        self,
        school_id: str,
        name: Optional[str] = None,
        address: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        pincode: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        principal_name: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Dict:
        """Update a school"""
        try:
            update_data = {}
            if name is not None:
                update_data["name"] = name
            if address is not None:
                update_data["address"] = address
            if city is not None:
                update_data["city"] = city
            if state is not None:
                update_data["state"] = state
            if pincode is not None:
                update_data["pincode"] = pincode
            if phone is not None:
                update_data["phone"] = phone
            if email is not None:
                update_data["email"] = email
            if principal_name is not None:
                update_data["principal_name"] = principal_name
            if is_active is not None:
                update_data["is_active"] = is_active
            
            if not update_data:
                raise APIException("No fields to update", 400)
            
            response = self.supabase.table("schools").update(update_data).eq("id", school_id).execute()
            
            if not response.data:
                raise APIException("School not found", 404)
            
            return response.data[0]
            
        except Exception as e:
            if isinstance(e, APIException):
                raise
            raise APIException(f"Error updating school: {str(e)}", 500)
    
    async def delete_school(self, school_id: str) -> Dict:
        """Delete a school"""
        try:
            response = self.supabase.table("schools").delete().eq("id", school_id).execute()
            
            return {"success": True, "message": "School deleted successfully"}
            
        except Exception as e:
            raise APIException(f"Error deleting school: {str(e)}", 500)
    
    async def assign_teacher_to_school(self, school_id: str, teacher_id: str) -> Dict:
        """Assign a teacher to a school"""
        try:
            # Check if user exists
            profile = self.supabase.table("profiles").select("*").eq("user_id", teacher_id).execute()
            if not profile.data:
                raise APIException("User not found", 404)
            
            # Check if user has teacher role, if not add it
            teacher_role = self.supabase.table("user_roles").select("*").eq("user_id", teacher_id).eq("role", "teacher").execute()
            if not teacher_role.data:
                # Add teacher role
                self.supabase.table("user_roles").insert({
                    "user_id": teacher_id,
                    "role": "teacher"
                }).execute()
            
            # Check if assignment already exists
            existing = self.supabase.table("school_teachers").select("*").eq("school_id", school_id).eq("teacher_id", teacher_id).execute()
            if existing.data:
                raise APIException("User is already assigned to this school as a teacher", 400)
            
            # Create assignment
            assignment_data = {
                "school_id": school_id,
                "teacher_id": teacher_id,
                "is_active": True
            }
            
            response = self.supabase.table("school_teachers").insert(assignment_data).execute()
            
            # Also update teacher_profile if exists
            teacher_profile = self.supabase.table("teacher_profiles").select("*").eq("user_id", teacher_id).execute()
            if teacher_profile.data:
                self.supabase.table("teacher_profiles").update({"school_id": school_id}).eq("user_id", teacher_id).execute()
            else:
                # Create teacher profile if it doesn't exist
                self.supabase.table("teacher_profiles").insert({
                    "user_id": teacher_id,
                    "school_id": school_id
                }).execute()
            
            return response.data[0] if response.data else assignment_data
            
        except Exception as e:
            if isinstance(e, APIException):
                raise
            import traceback
            error_msg = str(e)
            traceback.print_exc()
            raise APIException(f"Error assigning teacher: {error_msg}", 500)
    
    async def remove_teacher_from_school(self, school_id: str, teacher_id: str) -> Dict:
        """Remove a teacher from a school"""
        try:
            response = self.supabase.table("school_teachers").delete().eq("school_id", school_id).eq("teacher_id", teacher_id).execute()
            
            return {"success": True, "message": "Teacher removed from school"}
            
        except Exception as e:
            raise APIException(f"Error removing teacher: {str(e)}", 500)
    
    async def get_school_teachers(self, school_id: str) -> List[Dict]:
        """Get all teachers assigned to a school"""
        try:
            # Get school-teacher assignments
            assignments = self.supabase.table("school_teachers").select("*").eq("school_id", school_id).eq("is_active", True).execute()
            
            if not assignments.data:
                return []
            
            # Fetch teacher details
            teachers = []
            for assignment in assignments.data:
                teacher_id = assignment.get("teacher_id")
                if teacher_id:
                    # Get profile
                    profile = self.supabase.table("profiles").select("*").eq("user_id", teacher_id).execute()
                    # Get teacher profile
                    teacher_profile = self.supabase.table("teacher_profiles").select("*").eq("user_id", teacher_id).execute()
                    
                    teacher_data = {
                        "teacher_id": teacher_id,
                        "assigned_at": assignment.get("assigned_at"),
                        "profile": profile.data[0] if profile.data else None,
                        "teacher_profile": teacher_profile.data[0] if teacher_profile.data else None
                    }
                    teachers.append(teacher_data)
            
            return teachers
            
        except Exception as e:
            raise APIException(f"Error fetching school teachers: {str(e)}", 500)
    
    async def get_school_students(self, school_id: str, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get all students in a school"""
        try:
            # Get student profiles for the school
            student_profiles = self.supabase.table("student_profiles").select("*").eq("school_id", school_id).limit(limit).offset(offset).execute()
            
            if not student_profiles.data:
                return []
            
            # Get user IDs
            user_ids = [sp["user_id"] for sp in student_profiles.data]
            
            # Get profiles for these users
            profiles = self.supabase.table("profiles").select("*").in_("user_id", user_ids).execute()
            
            # Create a mapping of user_id to profile
            profile_map = {p["user_id"]: p for p in profiles.data or []}
            
            students = []
            for student_profile in student_profiles.data:
                user_id = student_profile.get("user_id")
                if user_id:
                    student_data = {
                        "user_id": user_id,
                        "class_grade": student_profile.get("class_grade"),
                        "school_name": student_profile.get("school_name"),
                        "profile": profile_map.get(user_id)
                    }
                    students.append(student_data)
            
            return students
            
        except Exception as e:
            import traceback
            error_msg = str(e)
            traceback.print_exc()
            raise APIException(f"Error fetching school students: {error_msg}", 500)
    
    async def assign_student_to_school(self, school_id: str, student_id: str) -> Dict:
        """Assign a student to a school"""
        try:
            # Check if student exists and has student role
            student_role = self.supabase.table("user_roles").select("*").eq("user_id", student_id).eq("role", "student").execute()
            if not student_role.data:
                raise APIException("User is not a student", 400)
            
            # Get school name
            school = await self.get_school(school_id)
            
            # Check if student profile exists
            existing_profile = self.supabase.table("student_profiles").select("*").eq("user_id", student_id).execute()
            
            if existing_profile.data:
                # Check if already assigned to this school
                existing_school_id = existing_profile.data[0].get("school_id")
                if existing_school_id == school_id:
                    raise APIException("Student is already assigned to this school", 400)
                
                # Update existing profile with new school
                class_grade = existing_profile.data[0].get("class_grade", 12)
                response = self.supabase.table("student_profiles").update({
                    "school_id": school_id,
                    "school_name": school.get("name")
                }).eq("user_id", student_id).execute()
            else:
                # Create new student profile
                # Try to get class_grade from profile metadata if available, otherwise default to 12
                profile = self.supabase.table("profiles").select("*").eq("user_id", student_id).execute()
                class_grade = 12  # Default
                if profile.data and profile.data[0].get("metadata"):
                    metadata = profile.data[0].get("metadata", {})
                    if isinstance(metadata, dict) and "class_grade" in metadata:
                        class_grade = metadata.get("class_grade", 12)
                
                response = self.supabase.table("student_profiles").insert({
                    "user_id": student_id,
                    "school_id": school_id,
                    "school_name": school.get("name"),
                    "class_grade": class_grade
                }).execute()
            
            return response.data[0] if response.data else {"success": True}
            
        except Exception as e:
            if isinstance(e, APIException):
                raise
            raise APIException(f"Error assigning student: {str(e)}", 500)
    
    async def get_all_teachers(self) -> List[Dict]:
        """Get all teachers in the system"""
        try:
            # Get all users with teacher role
            teacher_roles = self.supabase.table("user_roles").select("user_id").eq("role", "teacher").execute()
            teacher_ids = [tr["user_id"] for tr in teacher_roles.data or []]
            
            if not teacher_ids:
                return []
            
            # Get profiles
            profiles = self.supabase.table("profiles").select("*").in_("user_id", teacher_ids).execute()
            
            # Get teacher profiles
            teacher_profiles = self.supabase.table("teacher_profiles").select("*").in_("user_id", teacher_ids).execute()
            
            # Combine data
            teachers = []
            for profile in profiles.data or []:
                user_id = profile["user_id"]
                teacher_profile = next((tp for tp in teacher_profiles.data or [] if tp["user_id"] == user_id), None)
                
                teachers.append({
                    "user_id": user_id,
                    "profile": profile,
                    "teacher_profile": teacher_profile
                })
            
            return teachers
            
        except Exception as e:
            raise APIException(f"Error fetching teachers: {str(e)}", 500)
    
    async def get_all_users(self) -> List[Dict]:
        """Get all users in the system with their roles"""
        try:
            # Get all profiles
            profiles = self.supabase.table("profiles").select("*").execute()
            
            if not profiles.data:
                return []
            
            # Get all user roles
            user_ids = [p["user_id"] for p in profiles.data]
            
            # Handle empty user_ids list
            if not user_ids:
                return []
            
            # Get all user roles - handle case where there might be no roles
            roles_response = self.supabase.table("user_roles").select("*").in_("user_id", user_ids).execute()
            roles = roles_response.data or []
            
            # Get teacher profiles - handle case where there might be no teacher profiles
            teacher_profiles_response = self.supabase.table("teacher_profiles").select("*").in_("user_id", user_ids).execute()
            teacher_profiles = teacher_profiles_response.data or []
            
            # Get student profiles - handle case where there might be no student profiles
            student_profiles_response = self.supabase.table("student_profiles").select("*").in_("user_id", user_ids).execute()
            student_profiles = student_profiles_response.data or []
            
            # Combine data
            users = []
            for profile in profiles.data:
                user_id = profile.get("user_id")
                if not user_id:
                    continue
                    
                user_roles_list = [r.get("role") for r in roles if r.get("user_id") == user_id]
                teacher_profile = next((tp for tp in teacher_profiles if tp.get("user_id") == user_id), None)
                student_profile = next((sp for sp in student_profiles if sp.get("user_id") == user_id), None)
                
                users.append({
                    "user_id": user_id,
                    "profile": profile,
                    "roles": user_roles_list,
                    "teacher_profile": teacher_profile,
                    "student_profile": student_profile
                })
            
            return users
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Error in get_all_users: {str(e)}\n{error_trace}")
            raise APIException(f"Error fetching users: {str(e)}", 500)
    
    async def create_user(
        self,
        email: str,
        password: str,
        full_name: str,
        role: str,
        class_grade: Optional[int] = None,
        phone: Optional[str] = None,
        subject_specializations: Optional[List[str]] = None
    ) -> Dict:
        """Create a new user directly in Supabase"""
        try:
            # Use Supabase Admin API to create user directly
            # We'll use httpx but with proper error handling
            admin_url = f"{settings.supabase_url}/auth/v1/admin/users"
            headers = {
                "apikey": settings.supabase_service_key,
                "Authorization": f"Bearer {settings.supabase_service_key}",
                "Content-Type": "application/json"
            }
            
            user_data = {
                "email": email,
                "password": password,
                "email_confirm": True,
                "user_metadata": {
                    "full_name": full_name
                }
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                try:
                    response = await client.post(admin_url, json=user_data, headers=headers)
                    
                    # Supabase Admin API returns 200 for successful user creation
                    if response.status_code not in [200, 201]:
                        try:
                            error_json = response.json()
                            error_detail = (
                                error_json.get("msg") or 
                                error_json.get("message") or 
                                error_json.get("error_description") or 
                                error_json.get("error") or
                                f"HTTP {response.status_code}"
                            )
                        except:
                            error_detail = f"HTTP {response.status_code}: {response.text[:200]}"
                        
                        # Check for common errors
                        if "already registered" in error_detail.lower() or "already exists" in error_detail.lower() or "user already" in error_detail.lower():
                            raise APIException(f"User with email {email} already exists", 400)
                        
                        raise APIException(f"Error creating user: {error_detail}", response.status_code)
                    
                    try:
                        auth_user = response.json()
                    except Exception as e:
                        raise APIException(f"Invalid response from auth service: {str(e)}", 500)
                    
                    user_id = auth_user.get("id")
                    
                    if not user_id:
                        raise APIException("User created but no ID returned", 500)
                        
                except httpx.TimeoutException:
                    raise APIException("Request to Supabase timed out", 500)
                except httpx.RequestError as e:
                    raise APIException(f"Network error connecting to Supabase: {str(e)}", 500)
                
                # Create profile
                try:
                    profile_data = {
                        "user_id": user_id,
                        "full_name": full_name,
                        "profile_completed": True
                    }
                    profile_result = self.supabase.table("profiles").insert(profile_data).execute()
                    if not profile_result.data:
                        raise APIException("Failed to create profile", 500)
                except Exception as e:
                    # If profile creation fails, we should still try to clean up or at least log
                    import traceback
                    print(f"Error creating profile: {str(e)}\n{traceback.format_exc()}")
                    raise APIException(f"Error creating profile: {str(e)}", 500)
                
                # Add role
                try:
                    role_result = self.supabase.table("user_roles").insert({
                        "user_id": user_id,
                        "role": role
                    }).execute()
                    if not role_result.data:
                        raise APIException("Failed to create user role", 500)
                except Exception as e:
                    import traceback
                    print(f"Error creating user role: {str(e)}\n{traceback.format_exc()}")
                    raise APIException(f"Error creating user role: {str(e)}", 500)
                
                # Create role-specific profile
                try:
                    if role == "student":
                        # class_grade is required for students
                        if not class_grade:
                            # If class_grade not provided, default to 12
                            class_grade = 12
                        
                        student_profile_data = {
                            "user_id": user_id,
                            "class_grade": class_grade
                        }
                        student_result = self.supabase.table("student_profiles").insert(student_profile_data).execute()
                        if not student_result.data:
                            raise APIException("Failed to create student profile", 500)
                    elif role == "teacher":
                        teacher_profile_data = {
                            "user_id": user_id
                        }
                        if phone:
                            teacher_profile_data["phone"] = phone
                        if subject_specializations:
                            teacher_profile_data["subject_specializations"] = subject_specializations
                        teacher_result = self.supabase.table("teacher_profiles").insert(teacher_profile_data).execute()
                        if not teacher_result.data:
                            raise APIException("Failed to create teacher profile", 500)
                except Exception as e:
                    import traceback
                    print(f"Error creating {role} profile: {str(e)}\n{traceback.format_exc()}")
                    raise APIException(f"Error creating {role} profile: {str(e)}", 500)
                
                return {
                    "user_id": user_id,
                    "email": email,
                    "full_name": full_name,
                    "role": role
                }
                
        except APIException:
            raise
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Error in create_user: {str(e)}\n{error_trace}")
            raise APIException(f"Error creating user: {str(e)}", 500)


# Global instance
school_service = SchoolService()

