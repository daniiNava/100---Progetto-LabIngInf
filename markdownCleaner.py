class MarkdownCleaner():
    @staticmethod
    def clean(markdown_text : str) -> str:
        cleaned_text = markdown_text.replace("#","").replace("_", "").replace("*", "").replace("-", "").replace("+", "")
        return cleaned_text