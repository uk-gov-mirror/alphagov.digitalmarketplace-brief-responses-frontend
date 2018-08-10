from flask import escape, Markup
from flask_wtf import FlaskForm
from wtforms import validators

from dmutils.forms.fields import DMStripWhitespaceStringField


class AskClarificationQuestionForm(FlaskForm):
    """Form for a supplier to ask a clarification question about a given brief."""
    clarification_question = DMStripWhitespaceStringField(
        label="Ask a question",
        validators=[validators.DataRequired(message='Question cannot be empty'),
                    validators.Length(max=5000, message='Question cannot be longer than 5000 characters'),
                    validators.Regexp(regex="^$|(^(?:\\S+\\s+){0,99}\\S+$)",
                                      message='Question must be no more than 100 words')]
    )

    def __init__(self, brief, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.clarification_question.label.text = Markup(f'Ask a question about ‘{escape(brief["title"])}’')
        self.clarification_question.advice = (
            'Your question will be published with the buyer’s answer by {}. All questions and answers will be posted '
            'on the Digital Marketplace. Your company name won’t be visible. You shouldn’t include any confidential '
            'information in your question. Read more about <a href="https://www.gov.uk/guidance/how-to-answer-supplier-'
            'questions-about-your-digital-outcomes-and-specialists-requirements">how supplier questions are '
            'managed</a>.'
        )
