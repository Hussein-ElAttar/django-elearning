from django.contrib import admin
from django.db import connection, models
from django.db.models import Count
from django.utils.html import format_html

from quiz.forms import QuestionAdminForm
from quiz.models import Answer, Score
from quiz.widgets import AdminImageWidget

from .models import Category, Choice, Question


class AdminActionBtn():

    @admin.display(description='')
    def action_tag(self, obj):
        return format_html(f'<a href="{obj.get_admin_url()}" title="View"> <i class="fas fa-edit fa-sm"></i> </a>')


# Register your models here.
class ChoiceAdminInline(admin.TabularInline):
    model = Choice
    min_num = 1
    extra = 3
    formfield_overrides = {
        models.ImageField: {'widget': AdminImageWidget},
    }


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin, AdminActionBtn):
    search_fields = ('body',)
    list_filter = ('type', 'category', 'difficulty')
    list_display = ('body', 'image_tag', 'type', 'difficulty', 'category', 'action_tag')
    readonly_fields = ('renderedBody',)
    list_per_page = 10
    form = QuestionAdminForm
    inlines = [ChoiceAdminInline]

    # Preview Image in change view
    formfield_overrides = {
        models.ImageField: {'widget': AdminImageWidget},
    }

    # Move body & renderedBody to the beggining of the fieldset
    def get_fieldsets(self, request, obj=None):
        fs = super(QuestionAdmin, self).get_fieldsets(request, obj)
        fs[0][1]['fields'] = ['body', 'renderedBody'] + list((field for field in fs[0][1]['fields'] if field != 'body' and field != 'renderedBody'))
        return fs

    @admin.display(description='Preview')
    def renderedBody(self, obj):
        return format_html(f'<span class="renderedMathJax">{obj.body}<span/>')

    # Preview Image in List view
    @admin.display(description='Image')
    def image_tag(self, obj):
        return format_html(f'<img src="{obj.image.url}" style="height:150px;width: auto" />') if obj.image and obj.image.url else None



class QuestionAdminInline(admin.StackedInline):
    model = Question
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin, AdminActionBtn):
    inlines = [QuestionAdminInline]
    list_display = ['name', 'is_active', 'number_of_questions', 'action_tag']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(question_count=Count("question_category"))

    @admin.display(ordering='question_count', description='Questions Number')
    def number_of_questions(self, obj):
        return obj.question_count


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin, AdminActionBtn):
    list_display = ['user', 'question_body_image', 'user_answer', 'is_correct', 'action_tag']
    list_filter = ('user', 'question', 'is_correct')

    def get_fieldsets(self, request, obj=None):
        fs = super(AnswerAdmin, self).get_fieldsets(request, obj)
        fs[0][1]['fields'] = list((field for field in fs[0][1]['fields'] if field != 'question'))
        return fs

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields] + ['question_body_image']

    @admin.display(description='Question')
    def question_body_image(self, obj):
        return format_html(f'<span class="renderedMathJax">{obj.question.body}<span/>' + 
        f'<span><img src="{obj.question.image.url}" style="height:150px;width: auto" /><span/>' if obj.question.image and obj.question.image.url else None)


@admin.register(Score)
class ScoreAdmin(admin.ModelAdmin, AdminActionBtn):
    # Disable adding ones from dashboard
    list_display = ['student_name', 'category', 'total_score', 'action_tag']
    readonly_fields = ['user', 'category']

    def total_score(self, obj):
        return obj.value

    def student_name(self, obj):
        return obj.user.first_name + obj.user.last_name

    def has_add_permission(self, request):
        return False
