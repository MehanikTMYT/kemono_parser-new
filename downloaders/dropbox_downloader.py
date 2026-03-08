class DropboxDownloader:
    """Скачивание файлов с поддержкой cookies для авторизации"""
    
    def __init__(self, download_dir: str = "./downloads", dropbox_cookies: Optional[List[Dict]] = None):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self._logger = logging.getLogger("dropbox_downloader")
        self.session = requests.Session()
        
        # 🔹 Установка cookies если предоставлены
        if dropbox_cookies:
            self._setup_cookies(dropbox_cookies)
        
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
        })
    
    def _setup_cookies(self, cookies: List[Dict]):
        """Настройка cookies для сессии"""
        try:
            # Конвертация формата EditThisCookie в requests.cookies
            for cookie in cookies:
                self.session.cookies.set(
                    name=cookie['name'],
                    value=cookie['value'],
                    domain=cookie.get('domain', '.dropbox.com'),
                    path=cookie.get('path', '/'),
                    secure=cookie.get('secure', True)
                )
            
            self._logger.info(f"✅ Установлено {len(cookies)} cookies для Dropbox")
            
            # Проверка важных cookies
            important_cookies = ['sid', 'sidd', 'jar', 't']
            for cookie_name in important_cookies:
                if self.session.cookies.get(cookie_name, domain='.dropbox.com') or \
                   self.session.cookies.get(cookie_name, domain='.www.dropbox.com'):
                    self._logger.debug(f"   ✓ {cookie_name} установлен")
                else:
                    self._logger.warning(f"   ⚠ {cookie_name} не найден")
                    
        except Exception as e:
            self._logger.error(f"❌ Ошибка установки cookies: {e}")

    

    
    
    def download_folder(self, url: str, folder_name: str, skip_if_ru: bool = True) -> bool:
        """Скачать папку Dropbox как ZIP через Playwright"""
        if skip_if_ru:
            ip_info = self.check_ip()
            if ip_info["is_russia"]:
                self._logger.error(f"❌ Пропущено {folder_name}: РФ без VPN")
                return False
        
        filepath = self.download_dir / f"{folder_name}.zip"
        
        try:
            self._logger.info(f"⬇️ {folder_name} (папка)")
            
            # Запуск Playwright
            from playwright.sync_api import sync_playwright
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    viewport={"width": 1920, "height": 1080}
                )
                
                # Установка cookies если есть
                if hasattr(self, 'cookies') and self.cookies:
                    context.add_cookies(self.cookies)
                
                page = context.new_page()
                
                # Настройка загрузок
                page.set_default_timeout(120000)
                download_path = str(self.download_dir.absolute())
                
                with page.expect_download(timeout=180000) as download_info:
                    # Переход на страницу папки
                    page.goto(url, wait_until="domcontentloaded")
                    self._logger.debug(f"   Страница загружена")
                    
                    # Ждём появления кнопки Download
                    try:
                        # Пробуем найти кнопку "Download" или "Download as ZIP"
                        download_button = page.wait_for_selector(
                            'button[data-test="download-dropdown"], button:has-text("Download"), a[href*="?dl=1"]',
                            timeout=10000
                        )
                        
                        self._logger.debug(f"   Кнопка найдена, кликаю...")
                        
                        # Кликаем по кнопке
                        if download_button:
                            # Проверяем, есть ли dropdown
                            dropdown = page.query_selector('button[data-test="download-dropdown"]')
                            if dropdown:
                                dropdown.click()
                                page.wait_for_timeout(500)
                                # Кликаем по "Download as ZIP"
                                zip_option = page.wait_for_selector('text=Download as ZIP', timeout=5000)
                                if zip_option:
                                    zip_option.click()
                            else:
                                # Прямая кнопка
                                download_button.click()
                    
                    except Exception as e:
                        self._logger.warning(f"   ⚠️ Кнопка не найдена, пробуем прямую ссылку: {e}")
                        
                        # Альтернатива: конвертируем URL в прямую ссылку на ZIP
                        direct_url = self.convert_dropbox_url(url)
                        page.goto(direct_url, wait_until="domcontentloaded")
                        
                        # Пробуем ещё раз найти кнопку
                        try:
                            download_button = page.wait_for_selector(
                                'button:has-text("Download"), a[href*="?dl=1"]',
                                timeout=5000
                            )
                            if download_button:
                                download_button.click()
                        except:
                            pass
                
                # Ожидаем загрузку
                try:
                    download = download_info.value
                    self._logger.debug(f"   Загрузка началась...")
                    
                    # Сохраняем файл
                    download.save_as(str(filepath))
                    
                    size_mb = filepath.stat().st_size / 1024 / 1024
                    self._logger.info(f"✅ {folder_name}.zip ({size_mb:.1f} MB)")
                    
                    browser.close()
                    return True
                    
                except Exception as e:
                    self._logger.error(f"❌ Ошибка загрузки: {e}")
                    browser.close()
                    return False
        
        except Exception as e:
            self._logger.error(f"❌ Ошибка {folder_name}: {e}")
            if filepath.exists():
                filepath.unlink()
            return False

    def download_file(self, url: str, filename: str, skip_if_ru: bool = True) -> bool:
        """Скачать файл с поддержкой cookies"""
        if skip_if_ru:
            ip_info = self.check_ip()
            if ip_info["is_russia"]:
                self._logger.error(f"❌ Пропущено {filename}: РФ без VPN")
                return False
        
        direct_url = self.convert_dropbox_url(url)
        filepath = self.download_dir / filename
        
        try:
            self._logger.info(f"⬇️ {filename}")
            self._logger.debug(f"   URL: {direct_url[:100]}...")
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.9",
            }
            
            # HEAD запрос для проверки
            head_resp = self.session.get(direct_url, timeout=30, headers=headers, allow_redirects=True)
            
            if head_resp.status_code == 404:
                self._logger.error(f"❌ 404: {filename} — ссылка устарела")
                return False
            if head_resp.status_code == 403:
                self._logger.error(f"❌ 403: {filename} — доступ запрещён")
                return False
            
            content_type = head_resp.headers.get("content-type", "").lower()
            content_length = int(head_resp.headers.get("content-length", 0))
            
            # Проверка на HTML (страница входа)
            if "text/html" in content_type:
                if "sign in" in head_resp.text.lower() or "dropbox" in head_resp.text.lower():
                    self._logger.warning(f"⚠️ {filename} — требуется авторизация")
                    return False
            
            # Для папок Dropbox — проверяем размер
            if content_length < 1000 and "text/html" in content_type:
                self._logger.warning(f"⚠️ {filename} — возможно папка или неактивная ссылка")
                return False
            
            # Скачивание с прогрессом
            downloaded = 0
            with self.session.get(direct_url, timeout=300, headers=headers, stream=True) as resp:
                with open(filepath, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if content_length:
                                print(f"\r   {downloaded/content_length*100:.1f}%  ", end=" ", flush=True)
            
            print()
            
            # Финальная проверка
            if downloaded == 0 or filepath.stat().st_size < 500:
                try:
                    content = filepath.read_text(errors="ignore").lower()
                    if "<html" in content or "sign in" in content:
                        self._logger.warning(f"⚠️ {filename} — скачан как HTML, удаляю")
                        filepath.unlink()
                        return False
                except:
                    pass
                
                self._logger.warning(f"⚠️ {filename} — пустой файл, удаляю")
                if filepath.exists():
                    filepath.unlink()
                return False
            
            size_mb = downloaded / 1024 / 1024
            self._logger.info(f"✅ {filename} ({size_mb:.1f} MB)")
            return True
            
        except requests.exceptions.RequestException as e:
            self._logger.error(f"❌ Ошибка сети {filename}: {e}")
            if filepath.exists():
                filepath.unlink()
            return False
        except Exception as e:
            self._logger.error(f"❌ Ошибка {filename}: {e}")
            if filepath.exists():
                filepath.unlink()
            return False