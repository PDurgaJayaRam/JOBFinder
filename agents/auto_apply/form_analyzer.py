"""Application form analyzer - uses vision to identify form fields."""
import re
import base64
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from agents.vision_scraper.multi_provider_client import MultiProviderAIClient
from agents.vision_scraper.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class FieldType(str, Enum):
    TEXT = "text"
    EMAIL = "email"
    PHONE = "phone"
    NUMBER = "number"
    TEXTAREA = "textarea"
    SELECT = "select"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    FILE_UPLOAD = "file_upload"
    DATE = "date"
    URL = "url"
    SUBMIT = "submit"
    UNKNOWN = "unknown"


@dataclass
class FormField:
    """Represents a single form field."""
    field_id: str
    field_type: FieldType
    label: str
    placeholder: str
    required: bool
    x_coordinate: int
    y_coordinate: int
    width: int
    height: int
    options: List[str]
    value: str = ""
    needs_user_input: bool = False
    flag_reason: str = ""


@dataclass
class ScreeningQuestion:
    """Represents a screening question."""
    question_id: str
    question_text: str
    question_type: str  # yes_no, multiple_choice, text, number
    options: List[str]
    x_coordinate: int
    y_coordinate: int
    suggested_answer: str = ""
    needs_review: bool = False
    flag_reason: str = ""


@dataclass
class FormAnalysis:
    """Complete analysis of an application form."""
    url: str
    portal: str
    total_fields: int
    text_fields: List[FormField]
    select_fields: List[FormField]
    file_uploads: List[FormField]
    screening_questions: List[ScreeningQuestion]
    submit_button: Optional[FormField]
    estimated_fill_time_seconds: int
    fields_needing_review: List[str]
    can_auto_fill: bool


class FormAnalyzer:
    """Analyzes job application forms using vision and DOM inspection."""

    def __init__(self, ai_client: Optional[MultiProviderAIClient] = None):
        self.ai_client = ai_client
        self._field_counter = 0

    async def analyze_form_vision(
        self,
        screenshot_b64: str,
        portal: str = "unknown",
    ) -> Dict[str, Any]:
        """Use vision AI to analyze form layout and identify fields."""
        if not self.ai_client:
            return {"error": "AI client not available"}

        prompt = f"""
Analyze this job application form screenshot. Identify all form fields.

Return JSON:
{{
  "fields": [
    {{
      "label": "Field label text",
      "type": "text|email|phone|textarea|select|checkbox|file_upload|submit",
      "required": true/false,
      "x": coordinate,
      "y": coordinate,
      "placeholder": "placeholder text if visible"
    }}
  ],
  "screening_questions": [
    {{
      "question": "Question text",
      "type": "yes_no|multiple_choice|text|number",
      "options": ["option1", "option2"]
    }}
  ],
  "submit_button": {{"x": coordinate, "y": coordinate, "text": "button text"}},
  "total_fields": number,
  "portal": "{portal}"
}}
"""
        try:
            response = self.ai_client.vision_complete(
                image=base64.b64decode(screenshot_b64),
                prompt=prompt,
            )
            return response.get("parsed", {})
        except Exception as e:
            logger.error(f"Vision form analysis failed: {e}")
            return {"error": str(e)}

    async def analyze_form_dom(self, page) -> FormAnalysis:
        """Analyze form using DOM inspection (faster, no AI needed)."""
        try:
            form_data = await page.evaluate("""() => {
                const fields = [];
                const questions = [];
                let submitBtn = null;
                
                const inputs = document.querySelectorAll('input, textarea, select');
                inputs.forEach((el, i) => {
                    const type = el.type || el.tagName.toLowerCase();
                    const label = el.getAttribute('aria-label') || 
                                  el.getAttribute('placeholder') || 
                                  el.name || 
                                  el.id ||
                                  '';
                    
                    const rect = el.getBoundingClientRect();
                    
                    if (el.tagName.toLowerCase() === 'select') {
                        const options = Array.from(el.options).map(o => o.text);
                        fields.push({
                            field_id: el.id || `select_${i}`,
                            field_type: 'select',
                            label: label,
                            placeholder: el.getAttribute('placeholder') || '',
                            required: el.required || false,
                            x: Math.round(rect.x),
                            y: Math.round(rect.y),
                            width: Math.round(rect.width),
                            height: Math.round(rect.height),
                            options: options,
                            needs_user_input: false
                        });
                    } else if (type === 'file') {
                        fields.push({
                            field_id: el.id || `file_${i}`,
                            field_type: 'file_upload',
                            label: label,
                            placeholder: '',
                            required: el.required || false,
                            x: Math.round(rect.x),
                            y: Math.round(rect.y),
                            width: Math.round(rect.width),
                            height: Math.round(rect.height),
                            options: [],
                            needs_user_input: true,
                            flag_reason: 'Requires file upload'
                        });
                    } else if (type === 'submit' || el.tagName.toLowerCase() === 'button') {
                        if (el.innerText?.toLowerCase().includes('submit') || 
                            el.innerText?.toLowerCase().includes('apply') ||
                            type === 'submit') {
                            submitBtn = {
                                field_id: el.id || `submit_${i}`,
                                field_type: 'submit',
                                label: el.innerText?.trim() || 'Submit',
                                placeholder: '',
                                required: false,
                                x: Math.round(rect.x),
                                y: Math.round(rect.y),
                                width: Math.round(rect.width),
                                height: Math.round(rect.height),
                                options: [],
                                needs_user_input: false
                            };
                        }
                    } else {
                        let fieldType = 'text';
                        if (type === 'email' || label.toLowerCase().includes('email')) fieldType = 'email';
                        else if (type === 'tel' || label.toLowerCase().includes('phone')) fieldType = 'phone';
                        else if (type === 'number' || label.toLowerCase().includes('year') || label.toLowerCase().includes('salary')) fieldType = 'number';
                        else if (type === 'url' || label.toLowerCase().includes('linkedin') || label.toLowerCase().includes('portfolio')) fieldType = 'url';
                        else if (el.tagName.toLowerCase() === 'textarea') fieldType = 'textarea';
                        
                        const needsReview = label.toLowerCase().includes('cover letter') ||
                                           label.toLowerCase().includes('message') ||
                                           label.toLowerCase().includes('why') ||
                                           label.toLowerCase().includes('describe');
                        
                        fields.push({
                            field_id: el.id || `input_${i}`,
                            field_type: fieldType,
                            label: label,
                            placeholder: el.placeholder || '',
                            required: el.required || false,
                            x: Math.round(rect.x),
                            y: Math.round(rect.y),
                            width: Math.round(rect.width),
                            height: Math.round(rect.height),
                            options: [],
                            needs_user_input: needsReview,
                            flag_reason: needsReview ? 'Requires personalized content' : ''
                        });
                    }
                });
                
                // Detect screening questions
                const questionElements = document.querySelectorAll(
                    'label, .question, [class*="question"], [class*="screening"], ' +
                    'div[class*="question"], p[class*="question"]'
                );
                questionElements.forEach((el, i) => {
                    const text = el.innerText?.trim() || '';
                    if (text.length > 10 && text.length < 300 && 
                        (text.includes('?') || 
                         text.toLowerCase().includes('years') ||
                         text.toLowerCase().includes('authorized') ||
                         text.toLowerCase().includes('sponsor') ||
                         text.toLowerCase().includes('experience'))) {
                        const rect = el.getBoundingClientRect();
                        let qType = 'text';
                        const lower = text.toLowerCase();
                        if (lower.includes('yes') && lower.includes('no')) qType = 'yes_no';
                        else if (lower.includes('select') || lower.includes('choose')) qType = 'multiple_choice';
                        else if (lower.includes('year') || lower.includes('salary')) qType = 'number';
                        
                        questions.push({
                            question_id: `q_${i}`,
                            question_text: text,
                            question_type: qType,
                            options: [],
                            x: Math.round(rect.x),
                            y: Math.round(rect.y),
                            needs_review: qType === 'text',
                            flag_reason: ''
                        });
                    }
                });
                
                return {
                    fields: fields,
                    questions: questions,
                    submit_button: submitBtn
                };
            }""")

            text_fields = []
            select_fields = []
            file_uploads = []
            review_flags = []

            for f in form_data.get("fields", []):
                field = FormField(
                    field_id=f.get("field_id", ""),
                    field_type=FieldType(f.get("field_type", "unknown")),
                    label=f.get("label", ""),
                    placeholder=f.get("placeholder", ""),
                    required=f.get("required", False),
                    x_coordinate=f.get("x", 0),
                    y_coordinate=f.get("y", 0),
                    width=f.get("width", 0),
                    height=f.get("height", 0),
                    options=f.get("options", []),
                    needs_user_input=f.get("needs_user_input", False),
                    flag_reason=f.get("flag_reason", ""),
                )
                
                if f.get("needs_user_input"):
                    review_flags.append(f.get("label", "Unknown field"))
                
                if f.get("field_type") == "file_upload":
                    file_uploads.append(field)
                elif f.get("field_type") == "select":
                    select_fields.append(field)
                else:
                    text_fields.append(field)

            screening_questions = []
            for q in form_data.get("questions", []):
                screening_questions.append(ScreeningQuestion(
                    question_id=q.get("question_id", ""),
                    question_text=q.get("question_text", ""),
                    question_type=q.get("question_type", "text"),
                    options=q.get("options", []),
                    x_coordinate=q.get("x", 0),
                    y_coordinate=q.get("y", 0),
                    needs_review=q.get("needs_review", False),
                ))

            submit_btn = None
            if form_data.get("submit_button"):
                sb = form_data["submit_button"]
                submit_btn = FormField(
                    field_id=sb.get("field_id", ""),
                    field_type=FieldType.SUBMIT,
                    label=sb.get("label", "Submit"),
                    placeholder="",
                    required=False,
                    x_coordinate=sb.get("x", 0),
                    y_coordinate=sb.get("y", 0),
                    width=sb.get("width", 0),
                    height=sb.get("height", 0),
                    options=[],
                )

            total_fields = len(text_fields) + len(select_fields) + len(file_uploads)
            can_auto_fill = len(file_uploads) <= 1 and len(review_flags) <= 2
            estimated_time = total_fields * 5 + len(screening_questions) * 15

            url = page.url
            portal = self._detect_portal(url)

            return FormAnalysis(
                url=url,
                portal=portal,
                total_fields=total_fields,
                text_fields=text_fields,
                select_fields=select_fields,
                file_uploads=file_uploads,
                screening_questions=screening_questions,
                submit_button=submit_btn,
                estimated_fill_time_seconds=estimated_time,
                fields_needing_review=review_flags,
                can_auto_fill=can_auto_fill,
            )

        except Exception as e:
            logger.error(f"DOM form analysis failed: {e}")
            return FormAnalysis(
                url="",
                portal="unknown",
                total_fields=0,
                text_fields=[],
                select_fields=[],
                file_uploads=[],
                screening_questions=[],
                submit_button=None,
                estimated_fill_time_seconds=0,
                fields_needing_review=[f"Analysis error: {e}"],
                can_auto_fill=False,
            )

    def _detect_portal(self, url: str) -> str:
        """Detect job portal from URL."""
        if "naukri" in url:
            return "naukri"
        elif "linkedin" in url:
            return "linkedin"
        elif "indeed" in url:
            return "indeed"
        elif "glassdoor" in url:
            return "glassdoor"
        elif "cutshort" in url:
            return "cutshort"
        elif "timesjobs" in url:
            return "timesjobs"
        elif "shine" in url:
            return "shine"
        elif "foundit" in url:
            return "foundit"
        return "unknown"
