"""Reusable regulatory RAG backend shared by the notebook and Streamlit UI."""

import os
from pathlib import Path

import chromadb
import numpy as np
from dotenv import load_dotenv
from google import genai
from huggingface_hub import InferenceClient

load_dotenv(override=True)

HF_TOKEN = os.getenv("HF_TOKEN") or os.getenv("HF_Token")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


class RemoteHFEmbeddingFunction:
    """Chroma embedding adapter matching the index created in trails.ipynb."""

    def name(self):
        return "remote_huggingface"

    def _embed(self, texts):
        if isinstance(texts, str):
            texts = [texts]
        embeddings = _hf_client.feature_extraction(texts, model="BAAI/bge-m3")
        array = np.asarray(embeddings, dtype=np.float32)
        if array.ndim == 1:
            array = array.reshape(1, -1)
        return array.tolist()

    def __call__(self, input):
        return self._embed(input)

    def embed_query(self, input):
        return self._embed(input)


_hf_client = InferenceClient(token=HF_TOKEN)
_chroma_client = chromadb.PersistentClient(path=str(Path(__file__).with_name("chromadatabase")))
backend_collection = _chroma_client.get_collection(
    name="rag_db",
    embedding_function=RemoteHFEmbeddingFunction(),
)
_gemini_client = genai.Client(api_key=GEMINI_API_KEY)


def answer_from_backend(query: str, n_results: int = 3):
    """Retrieve regulatory context and generate an answer with source metadata."""
    result = backend_collection.query(query_texts=[query], n_results=n_results)
    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    context_entries = []
    sources = []

    for document, metadata in zip(documents, metadatas):
        metadata = metadata or {}
        source = (
            metadata.get("source")
            or metadata.get("doc_name")
            or metadata.get("Source")
            or "مستند غير محدد"
        )
        page = metadata.get("page", "?")
        context_entries.append(f"[المستند: {source} | صفحة: {page}]\n{document}")
        sources.append({"source": source, "page": page})

    formatted_text = "\n\n---\n\n".join(context_entries)

    prompt = f"""أنت مستشار قانوني ومصرفي أول متخصص في التعليمات الرقابية الصادرة عن البنك المركزي المصري ووحدة مكافحة غسل الأموال.

مهمتك: تقديم تقرير تنظيمي متكامل ومهني للإجابة عن استفسار العميل، بصياغة مصرفية مؤسسية جاهزة للعرض المباشر، مع الالتزام التام بالضوابط التالية:

1. المعالجة الصامتة للأرقام (Silent Normalization):
- عند وجود أي تعارض بين الرموز الرقمية (Digits) والتفقيط المكتوب بالحروف (مثل "7٠٠٠٠١" مع "عشرون ألف"): اعتمد دائماً التفقيط النصي بالحروف.
- اكتب الرقم الحسابي الصحيح المتطابق مع النص مباشرة وبالصيغة القياسية (مثال: 20,000 (عشرون ألف) جنيه مصري).
- يُحظر تماماً وقطعياً ذكر أي مصطلحات تقنية أو تبريرات مثل: "خطأ OCR"، "مسح ضوئي"، "أخطاء رقمية"، "تم تصحيح الرقم"، أو "رقم مشوه". اعرض الرقم النهائي السليم بانسيابية تامة وكأنه الأصل دون أي تلميح لوجود خطأ سابق.

2. التعامل مع البيانات غير المتاحة:
- إذا لم يشتمل النص المرفق على بيان محدد أو لم يُذكر الرقم المالي: وضّح ذلك بأسلوب رسمي ولبق (مثال: "لم تتضمن التعليمات التنظيمية المتاحة حداً مالياً يومياً صريحاً لهذه الفئة").
- يُمنع إلقاء اللوم على "انقطاع النص" أو "مشاكل الاستخراج".

3. الصياغة وهيكلة المخرجات (التحليل أولاً ثم المراجع):
- اكتب الإجابة بأسلوبك المصرفي الخاص في صورة ملخص تنفيذي يليه تفصيل البنود في نقاط أو جداول واضحة ومقروءة.
- تجنب حشو التوثيق (اسم المستند ورقم الصفحة) داخل كل سطر أو بين الجمل والفقرات التحليلية.
- ضع قسماً مستقلاً في نهاية التقرير بعنوان: "المصادر والوثائق التنظيمية المعتمدة"، يوضح المستندات وأرقام الصفحات المستند إليها.

قواعد التنسيق الشكلي (Plain Text):
- اكتب الإجابة كنص عادي انسيابي تماماً بدون استخدام علامات تنسيق Markdown نهائياً.
- يُمنع منعاً باتاً استخدام الرموز التالية:
  * الهاشتاج (#، ##، ###)
  * النجوم المتكررة (**)
  * الفواصل الأفقية (---)
  * جداول الماركداون (|)
- قسّم الفقرات بأسطر فارغة، واستخدم الترقيم البسيط (1. 2. 3.) أو النقاط العادية (•) لتوضيح البنود.
السياق التنظيمي المتاح:
{formatted_text}

استفسار العميل:
{query}
"""
    response = _gemini_client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
    )
    return response.text, sources


backend_collection_count = backend_collection.count()
