from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.
class userAccount(models.Model):
    class user_type(models.TextChoices):
        STUDENT = "student", "Student"
        RECRUITER = "recruiter", "Recruiter"

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name="profile")
    profile_image = models.FileField(upload_to="profileImages/", blank=True, null=True)
    usertype = models.CharField(max_length=20, choices=user_type.choices, default=user_type.STUDENT)
    job_title = models.CharField(max_length=50, null=True, blank=True)
    bio = models.TextField(max_length=100, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    is_onboarded = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s account"
    


class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class UserSkill(models.Model):
    class Status(models.TextChoices):
        NOT_STARTED = "not_started", "Not Started"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"

    user = models.ForeignKey(userAccount, on_delete=models.SET_NULL, null=True, blank=True, related_name="user_skills")
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name="skills")
    status = models.CharField(max_length=15,choices=Status.choices, default=Status.NOT_STARTED)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "skill")
        indexes = [
            models.Index(fields=["user", "status"]),
        ]

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def __str__(self):
        return f"{self.user} - {self.skill.name} ({self.status})"



class Quiz(models.Model):
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name="quizzes")
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    total_marks = models.PositiveIntegerField(default=10)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.skill.name}"



class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    question_text = models.TextField()
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    correct_option = models.CharField(max_length=1, choices=[("A", "A"), ("B", "B"), ("C", "C"), ("D", "D")])
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return self.question_text


class UserQuizResult(models.Model):
    user = models.ForeignKey(userAccount, on_delete=models.CASCADE, related_name="quiz_results")
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="results")
    score = models.PositiveIntegerField(default=0)
    completed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.user.username} - {self.quiz.title} - {self.score}"



class UserAnswer(models.Model):
    user = models.ForeignKey(userAccount, on_delete=models.CASCADE, related_name="user_answers")
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="user_answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="user_answers")
    selected_option = models.CharField(max_length=1, choices=[("A", "A"), ("B", "B"), ("C", "C"), ("D", "D")])
    is_correct = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "question")

    def __str__(self):
        return f"{self.user} - Q{self.question.id}: {self.selected_option}"

