from rest_framework import serializers
from django.contrib.auth.models import User
from users.models import userAccount, Skill, UserSkill, Quiz, Question, UserQuizResult, UserAnswer


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']


class UserAccountSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = userAccount
        fields = [
            'id', 'user', 'profile_image', 'usertype', 'job_title',
            'bio', 'is_verified', 'is_active', 'created_at', 'updated_at'
        ]



class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ['id', 'name', 'description', 'created_at', 'updated_at']



class UserSkillSerializer(serializers.ModelSerializer):
    # user = UserAccountSerializer(read_only=True)
    skill = SkillSerializer(read_only=True)

    class Meta:
        model = UserSkill
        fields = [
            'id', 'user', 'skill', 'status', 'is_deleted',
            'deleted_at', 'created_at', 'updated_at'
        ]



class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = [
            'id', 'quiz', 'question_text', 'option_a', 'option_b',
            'option_c', 'option_d', 'created_at'
        ]


class QuizSerializer(serializers.ModelSerializer):
    skill = SkillSerializer(read_only=True)
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = ['id', 'skill', 'questions', 'title', 'description', 'total_marks', 'created_at']


class UserQuizResultSerializer(serializers.ModelSerializer):
    quiz_title = serializers.CharField(source='quiz.title', read_only=True)
    quiz_description = serializers.CharField(source='quiz.description', read_only=True)

    class Meta:
        model = UserQuizResult
        fields = ['id', 'user', 'quiz_title', 'quiz_description', 'score', 'completed_at']


class UserAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAnswer
        fields = ['id', 'user', 'quiz', 'question', 'selected_option', 'is_correct', 'answered_at']
        read_only_fields = ['is_correct', 'answered_at']