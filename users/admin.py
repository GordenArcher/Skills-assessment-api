from django.contrib import admin
from .models import userAccount, UserSkill, UserQuizResult, Question, Quiz, Skill, UserAnswer

# Register your models here.

@admin.register(userAccount)
class userAccountAdmin(admin.ModelAdmin):
    list_display = ("user", "profile_image", "usertype", "job_title", "bio", "is_verified", "is_onboarded", "is_active", "created_at", "updated_at")
    list_filter = ("user", "usertype", "job_title", "is_verified", "is_onboarded", "is_active", "created_at")
    search_fields = ("user", "profile_image", "usertype", "job_title", "bio", "is_verified", "is_onboarded", "is_active", "created_at", "updated_at")
    
    def __str__(self):
        return f"{self.user} - {self.usertype}"
    


@admin.register(UserSkill)
class UserSkillAdmin(admin.ModelAdmin):
    list_display = ("user", "skill", "status", "is_deleted", "deleted_at", "created_at", "updated_at")
    list_filter = ("user", "skill", "status", "is_deleted", "created_at")
    search_fields = ("user", "skill", "status", "is_deleted")

    def __str__(self):
        return f"skill - {self.skill} for {self.user}"
    


@admin.register(UserQuizResult)
class UserQuizResultAdmin(admin.ModelAdmin):
    list_display = ("user", "quiz", "score", "completed_at")
    list_filter = ("user", "quiz", "score", "completed_at")
    search_fields = ("user", "quiz", "score", "completed_at")

    def __str__(self):
        return f"result score ({self.score}) for {self.user}"
    


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("quiz", "question_text", "option_a", "option_b", "option_c", "option_d", "correct_option", "created_at")
    list_filter = ("quiz", "question_text", "option_a", "option_b", "option_c", "option_d", "correct_option", "created_at")
    search_fields = ("quiz", "question_text", "option_a", "option_b", "option_c", "option_d", "correct_option")

    def __str__(self):
        return f"question for {self.quiz}"



@admin.register(Quiz)
class Quiz(admin.ModelAdmin):
    list_display = ("skill", "title", "description", "total_marks", "created_at")
    list_filter = ("skill", "title", "description", "total_marks", "created_at")
    search_fields = ("skill", "title", "description", "total_marks")

    def __str__(self):
        return f"question for skill ({self.skill})"
    



@admin.register(Skill)
class Skill(admin.ModelAdmin):
    list_display = ("name", "description", "created_at", "updated_at")
    list_filter = ("name", "description", "created_at")
    search_fields = ("name", "description", )

    def __str__(self):
        return f"{self.name}"
    


@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ('user', 'quiz', 'question', 'selected_option', 'is_correct', 'submitted_at')
    list_filter = ('quiz', 'is_correct', 'submitted_at')
    search_fields = ('user__username', 'question__question_text')
