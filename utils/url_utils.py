def convert_dropbox_url(self, url: str) -> str:
        """Конвертация ссылки Dropbox"""
        import re
        url = url.strip()
        
        # Ссылки на отдельные файлы: /s/
        if "dropbox.com/s/" in url and "scl" not in url and "/sh/" not in url:
            url = re.sub(r'[?&]dl=[01]', '', url)
            sep = "&" if "?" in url else "?"
            return f"{url}{sep}dl=1"
        
        # Ссылки на папки: /scl/fo/ и /sh/
        elif "dropbox.com/scl/fo/" in url or "dropbox.com/sh/" in url:
            url = re.sub(r'[?&]dl=0', '', url)
            sep = "&" if "?" in url else "?"
            return f"{url}{sep}dl=1"
        
        return url