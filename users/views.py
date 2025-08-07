from django.shortcuts import render
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework import status
from django.contrib.auth import login as auth_login, get_user_model, authenticate
from django.contrib import auth
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from core.utils.responses import success_response, error_response
from .serializers.auth import LoginSerializer, RegisterSerializer, ChangePasswordSerializer
from .serializers.serializers import UserSkillSerializer, UserAccountSerializer, QuizSerializer, QuestionSerializer, UserQuizResultSerializer, SkillSerializer
from .tasks import send_verification_email, send_reset_password_request_email
from .models import userAccount, UserSkill, Skill, Quiz, UserQuizResult, Question, UserAnswer
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from rest_framework.throttling import UserRateThrottle
from rest_framework.decorators import throttle_classes
# Create your views here.


class FivePerMinuteThrottle(UserRateThrottle):
    rate = '5/minute'

class customTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.COOKIES.get("refresh_token")
            if not refresh_token:
                return error_response("No refresh token found in cookies.", {"detail": "refresh token was not found in the cookies."}, status.HTTP_401_UNAUTHORIZED)

            request._full_data = request.data.copy()
            request._full_data['refresh'] = refresh_token

            response = super().post(request, *args, **kwargs)

            access_token = response.data['access']

            res = success_response("Token has been refrshed", { "refreshed": True, "token": access_token })

            res.set_cookie(
                key="access_token",
                value=access_token,
                secure=False,
                httponly=True,
                samesite='None',
                path='/',
                max_age=60 * 10,
            )

            res.set_cookie(
                key="isLoggedIn",
                value=True,
                secure=True,
                httponly=True,
                samesite='None',
                path='/',
                max_age=60 * 10,
            )

            return res

        except Exception as e:
            return error_response("An unexpected error occured", { "refreshed": False, "message":f"{e}"}, status.HTTP_500_INTERNAL_SERVER_ERROR)
       


@api_view(["POST"])
@authentication_classes([])
@throttle_classes([FivePerMinuteThrottle])
def login(request):
    serializer = LoginSerializer(data=request.data)

    if not serializer.is_valid():
        return error_response("Validation failed", serializer.errors)

    email = serializer.validated_data["email"]
    password = serializer.validated_data["password"]

    try:
        user = get_user_model().objects.get(email=email)
    except get_user_model().DoesNotExist:
        return error_response("Email is not associated with any user", "Invalid user email")
    
    try:
        profile = userAccount.objects.get(user=user)
    except userAccount.DoesNotExist:    
        return error_response("User profile not found", {"details": "No profile associated with this user"}, status.HTTP_404_NOT_FOUND) 
       

    # if not profile.is_verified:
    #     return error_response("Please verify your email", {"details": "Email hasn't been verified yet"}, status.HTTP_403_FORBIDDEN)



    if not check_password(password, user.password):
        return error_response("Invalid credentials", { "detail": "Invalid email or password" }, status.HTTP_401_UNAUTHORIZED)

    auth_login(request, user)

    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)

    response = success_response("Login successful", { "access_token": access_token, "auth": True})

    cookie_settings = {
        "path": "/",
        "samesite": "Lax",
        "secure": False,
        "httponly": True
    }

    response.set_cookie(
        key="access_token", 
        value=str(access_token), 
        max_age=60*10, 
        **cookie_settings
    )

    response.set_cookie(
        key="refresh_token", 
        value=str(refresh), 
        max_age=60*60*24*7, 
        **cookie_settings
    )

    response.set_cookie(
        key="is_loggedIn", 
        value=bool(True), 
        max_age=60*10, 
        **cookie_settings
    )

    return response



@api_view(["POST"])
def register(request):

    serializer = RegisterSerializer(data = request.data)

    if not serializer.is_valid():
        return error_response("Validation failed", serializer.errors)
    
    first_name = serializer.validated_data["first_name"]
    last_name = serializer.validated_data["last_name"]
    username = serializer.validated_data["username"]
    email = serializer.validated_data["email"]
    password = serializer.validated_data["password"]
    password2 = serializer.validated_data["password2"]

    try:

        if password != password2:
            return error_response("Password mismatch.", { "details": "Password and confirm password do not match."})

        if User.objects.filter(email=email).exists():
            return error_response("User with this email already exists.", {"details" : "Email conflict occured! it's already associated with another user"}, status.HTTP_409_CONFLICT)
            

        if User.objects.filter(username=username).exists():
            return error_response("Username already in use.", {"details" : "Username conflict occured! it's already associated with another user"}, status.HTTP_409_CONFLICT)
            

        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password
        )

        user_account = userAccount.objects.create(user=user)
        user_account.is_verified = False
        user_account.save()

        send_verification_email.delay(user.id)

        return success_response("User registered successfully.", { "url": "/auth/login" }, status.HTTP_201_CREATED)
        

    except Exception as e:
        return error_response("An unexpected error occured", { "details": "Failed to registrater user", }, status.HTTP_500_INTERNAL_SERVER_ERROR)
       



@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    try:
        auth.logout(request)

        res = success_response("You logged out successfully", { "authenticated": False })

        cookie_settings = { "path": "/", "samesite": "None" }

        res.delete_cookie(
            key="access_token",
            **cookie_settings
        )
        res.delete_cookie(
            key="refresh_token", 
            **cookie_settings
        )
        res.delete_cookie(
            key="isLoggedIn", 
            **cookie_settings
        )

        return res

    except Exception as e:
        return error_response("An unexpected error occured", { "details": f"Failed to logout user {e}", }, status.HTTP_500_INTERNAL_SERVER_ERROR)
       



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_authentication(request):
    try:

        return success_response("authenticated", { "auth": True, })

    except Exception as e:
        return error_response("An unexpected error occured", { "details": "Failed to get authentication status", }, status.HTTP_500_INTERNAL_SERVER_ERROR)     
           



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    serializer = ChangePasswordSerializer(data = request.data)
   
    try:
       
        if not serializer.is_valid():
            return error_response("Validation failed", serializer.errors)
        
        old_password = serializer.validated_data["currentPassword"]
        new_password = serializer.validated_data["newPassword"]
        new_password2 = serializer.validated_data["confirmPassword"]

        if new_password != new_password2:
           return error_response("New passwords do not match", {"details":"New Passwords mismatch"})

        user = request.user

        if not user.check_password(old_password):
            return error_response("Current password is incorrect", {"details": "Current password input is not correct"})

        if user.check_password(new_password):
            return error_response("New password cannot be the same as the current password", {"details":"Password conflict, new password can't be set as current password"}, status.HTTP_409_CONFLICT)

        try:
            validate_password(new_password, user=user)
        except ValidationError as ve:
            return error_response("Weak password", {"details": ve.messages}, status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        return success_response("Password has been changed successful")


    except Exception as e:
        return error_response("An unexpected error occured", { "details": "Failed to update password"}, status.HTTP_500_INTERNAL_SERVER_ERROR)
            



@api_view(["POST"])
def reset_password_request_email(request):
    email = request.data.get("email")

    try:

        if not email:
            return error_response("Email field cannot be empty", {"details":"Email field was empty"})

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return error_response("Email does not exist", {"details":"Email entered is not associated with any user"}, status.HTTP_404_NOT_FOUND) 
        

        send_reset_password_request_email.delay(user.id, email)

        return success_response("An email has been sent to you")


    except Exception as e:
        return error_response("An unexpected error occured", { "details": "Failed sending user email", "message":f"{e}" }, status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(["POST"])
@authentication_classes([])
def reset_password_request(request):
    data = request.data
    uidb64 = data.get("uid")
    token = data.get("token")
    new_password = data.get("newPassword")
    new_password2 = data.get("confirmPassword")

    try:
        if not uidb64 or not token:
            return error_response("Invalid link.")
        

        if not new_password or not new_password2:
            return error_response("Both fields are required", {"details":"Both new password and confirm password are required"})
        

        if new_password != new_password2:
           return error_response("New passwords do not match", {"details":"New Passwords mismatch"})

        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            return error_response("Invalid user.", {"details":"User was not found"}, status.HTTP_404_NOT_FOUND)


        if default_token_generator.check_token(user, token):
            if user.check_password(new_password):
                return error_response("New password cannot be the same as the current password", {"details":"Password conflict, new password can't be set as current password"}, status.HTTP_409_CONFLICT)
            
            try:
                validate_password(new_password, user=user)
            except ValidationError as ve:
                return error_response("Weak password", {"details": ve.messages}, status.HTTP_400_BAD_REQUEST)
    
            user.set_password(new_password)
            user.save()

            return success_response("Password sucessfully updated")

        else:
            return error_response("Invalid or expired token and uid.", {"details":"Token or uid is invalid"})


    except Exception as e:
        return error_response("An unexpected error occured", { "details": "Failed reseting user password"}, status.HTTP_500_INTERNAL_SERVER_ERROR)




@api_view(["POST"])
@authentication_classes([])
def verify_email(request):
    uidb64 = request.data.get("uid")
    token = request.data.get("token")

    try:
        if not uidb64 or not token:
            return error_response("Invalid link.")

        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            return error_response("Invalid user.", {"details":"User was not found"},status.HTTP_404_NOT_FOUND)


        if default_token_generator.check_token(user, token):
            user.profile.is_verified = True
            user.profile.save()
            return success_response("Email successfully verified.", { "verified": True})
        
        else:
            return error_response("Invalid or expired token and uid.", {"details":"Token or uid is invalid"})


    except Exception as e:
        return error_response("An unexpected error occured", { "details": "Failed to verify email"}, status.HTTP_500_INTERNAL_SERVER_ERROR)




@api_view(["POST"])
@permission_classes([IsAuthenticated])
def onboarding(request):
    skills = request.data.get("skills")

    if not skills:
        return error_response("Skill is required", {"details": "Skills field is empty"})

    if not isinstance(skills, list):
        return error_response("Invalid data type", {"details": "Skills should be a list"})

    try:
        try:
            user = userAccount.objects.get(user=request.user)
        except userAccount.DoesNotExist:
            return error_response("User not found", {"details": "User profile not created"}, status.HTTP_404_NOT_FOUND)

        for skill_name in skills:
            try:
                skill = Skill.objects.get(name=skill_name)

                if not UserSkill.objects.filter(user=user, skill=skill).exists():
                    UserSkill.objects.create(user=user, skill=skill, status="not_started")
            except Skill.DoesNotExist:
                continue

        user.is_onboarded = True
        user.save()

        return success_response("Onboarding completed", {"onboarded": True, "url": "/"}, status.HTTP_201_CREATED)

    except Exception as e:
        return error_response("Unexpected error", {"details": str(e)}, status.HTTP_500_INTERNAL_SERVER_ERROR)




@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_user(request):
    try:
        try:
            user = userAccount.objects.get(user=request.user)
        except userAccount.DoesNotExist:
            return error_response("User not found", {"details": "User profile not created"}, status.HTTP_404_NOT_FOUND)
        
        serializer = UserAccountSerializer(user)

        return success_response("retrieved", {"user": serializer.data})

    except Exception as e:
        return error_response("Unexpected error", {"details": str(e)}, status.HTTP_500_INTERNAL_SERVER_ERROR)




@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_user_skills(request):
    try:
        try:
            user = userAccount.objects.get(user=request.user)
        except userAccount.DoesNotExist:
            return error_response("User not found", {"details": "User profile not created"}, status.HTTP_404_NOT_FOUND)
        
        user_skills = UserSkill.objects.filter(user=user)

        serializer = UserSkillSerializer(user_skills, many=True)

        return success_response("retrieved", {"skills": serializer.data})

    except Exception as e:
        return error_response("Unexpected error", {"details": str(e)}, status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([])
def get_all_questions(request):
    try:

        question = Question.objects.all()

        question_serializer = QuestionSerializer(question, many=True)

        return success_response("retrieved", {"question":question_serializer.data})

    except Exception as e:
        return error_response("Unexpected error", {"details": str(e)}, status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_user_quiz(request):
    try:
        user = request.user
        user_profile = user.profile.first() 

        if not user_profile:
            return error_response("User profile not found", status.HTTP_404_NOT_FOUND)

        user_skills = UserSkill.objects.filter(user=user_profile, is_deleted=False).values_list("skill", flat=True)

        quizzes = Quiz.objects.filter(skill__id__in=user_skills)

        serializer = QuizSerializer(quizzes, many=True)

        return success_response("retrieved user quizes", {"quizzes": serializer.data})

    except Exception as e:
        return error_response("Unexpected error", {"details": str(e)}, status.HTTP_500_INTERNAL_SERVER_ERROR)




@api_view(["POST"])
@permission_classes([IsAuthenticated])
def submit_quiz(request):
    try:
        data = request.data
        quiz_id = data.get("quiz_id")
        answers = data.get("answers", [])

        if not quiz_id or not answers:
            return error_response(
                "quiz_id and answers are required", 
                {"details": "Please provide both 'quiz_id' and a list of 'answers' in the request body. 'answers' should be a list of objects, each containing a 'question_id' and the selected 'option_id'."}, 
                status.HTTP_400_BAD_REQUEST)
        
        try:
            user = userAccount.objects.get(user=request.user)
        except userAccount.DoesNotExist:    
            return error_response("User profile not found", status.HTTP_404_NOT_FOUND)


        quiz = Quiz.objects.get(id=quiz_id)

        if UserQuizResult.objects.filter(user=user, quiz=quiz).exists():
            return error_response("You have already submitted this quiz.", {"details":"Each user can only attempt a quiz once."}, status.HTTP_400_BAD_REQUEST)

        score = 0
        wrong_answers = []

        for ans in answers:
            question_id = ans.get("question_id")
            selected = ans.get("selected_option", "").upper()

            if not question_id or selected not in ["A", "B", "C", "D"]:
                continue

            try:
                question = Question.objects.get(id=question_id, quiz=quiz)
            except Question.DoesNotExist:
                continue

            is_correct = (selected == question.correct_option)

            user_answers = UserAnswer.objects.create(
                user=user,
                quiz=quiz,
                question=question,
            )

            user_answers.selected_option = selected
            user_answers.is_correct = is_correct
            user_answers.save()

            if is_correct:
                score += 1


            if not is_correct:
                wrong_answers.append({
                    "question_id": question.id,
                    "selected_option": selected,
                    "correct_option": question.correct_option
                })    

        UserQuizResult.objects.create(user=user, quiz=quiz, score=score)

        return success_response(
            "Quiz submitted successfully",
            {"score": score, 
             "total": len(answers),
             "wrong_answers": wrong_answers
            },
            status.HTTP_200_OK
        )

    except Exception as e:
        return error_response("Unexpected error", {"details": str(e)}, status.HTTP_500_INTERNAL_SERVER_ERROR)




@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_user_quiz_results(request):
    try:

        try:
            user = userAccount.objects.get(user=request.user)
        except userAccount.DoesNotExist:    
            return error_response("User profile not found", status.HTTP_404_NOT_FOUND)


        results = UserQuizResult.objects.filter(user=user).select_related("quiz")

        results_serializer = UserQuizResultSerializer(results, many=True)

        return success_response("retrieved", { "results":results_serializer.data })


    except Exception as e:
        return error_response("Unexpected error", {"details": str(e)}, status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(["GET"])
@permission_classes([])
def all_skills(request):

    try:

        skills = Skill.objects.all()

        skills_serializer = SkillSerializer(skills, many=True)

        return success_response("retrieved skills", {"skills": skills_serializer.data})


    except Exception as e:
        return error_response("Unexpected error", {"details": str(e)}, status.HTTP_500_INTERNAL_SERVER_ERROR)
