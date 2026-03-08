"""
Kemono клиент через Playwright с полной функциональностью.
"""

from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page, Route
from typing import Dict, List, Optional, Set
import time
import logging

logger = logging.getLogger(__name__)


class KemonoPlaywrightClient:
    BASE_URL = "https://kemono.cr"
    
    AD_DOMAINS = [
        "cdn.tsyndicate.com", "pxl-eu.tsyndicate.com", "tsvideo.sacdnssedge.com",
        "static-proxy.strpst.com", "doubleclick.net", "googlesyndication.com",
        "adsbygoogle.com", "adnxs.com", "adsrvr.org", "taboola.com",
        "outbrain.com", "popads.net", "pushengage.com"
    ]
    
    AD_PATH_PATTERNS = [
        "/sdk/v1/n.js", "/sdk/v1/outstream.video.js", "/api/v1/p/p.gif",
        "ts_ad_", "mn-", "outstream-video", "ad-container", "sponsor", "promo"
    ]

    def __init__(
        self,
        headless: bool = True,
        session_cookie: Optional[str] = None,
        timeout: int = 60000,
        block_ads: bool = True,
        block_18plus: bool = True
    ):
        self.headless = headless
        self.session_cookie = session_cookie.strip() if session_cookie else None
        self.timeout = timeout
        self.block_ads = block_ads
        self.block_18plus = block_18plus
        
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._logger = logging.getLogger("playwright.kemono")

    def start(self) -> bool:
        """Запуск браузера"""
        try:
            self.playwright = sync_playwright().start()
            
            browser_args = [
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ]
            
            self.browser = self.playwright.chromium.launch(
                headless=self.headless,
                args=browser_args,
                ignore_default_args=["--enable-automation"]
            )
            
            self.context = self.browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="en-US",
                accept_downloads=False
            )
            
            self.context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            """)
            
    
            if self.block_ads:
                def block_routes(route: Route):
                    url = route.request.url.lower()
                    if any(domain in url for domain in self.AD_DOMAINS):
                        return route.abort("blockedbyclient")
                    if any(pattern in url for pattern in self.AD_PATH_PATTERNS):
                        return route.abort("blockedbyclient")
                    return route.continue_()
                self.context.route("**/*", block_routes)
            
            self.page = self.context.new_page()
            
     
            def handle_download(download):
                try:
                    download.cancel()
                except:
                    pass
            self.page.on("download", handle_download)
            
     
            if self.session_cookie:
                self.context.add_cookies([{
                    "name": "session",
                    "value": self.session_cookie,
                    "domain": ".kemono.cr",
                    "path": "/",
                    "secure": True,
                    "httpOnly": True
                }])
                self._logger.info("✅ Session cookie установлен")
            
            # Навигация
            if not self._goto(self.BASE_URL):
                time.sleep(3)
                if not self._goto(self.BASE_URL):
                    return False
            
            if self.block_ads or self.block_18plus:
                self._inject_adblocker()
            
            self._logger.info("✅ Браузер запущен")
            return True
            
        except Exception as e:
            self._logger.error(f"❌ Ошибка запуска: {e}", exc_info=True)
            return False

    def _goto(self, url: str, wait_until: str = "domcontentloaded") -> bool:
        if not self.page:
            return False

        try:
            self.page.goto(url, wait_until=wait_until, timeout=self.timeout)
            self.page.wait_for_load_state("networkidle", timeout=10000)
            return True

        except Exception as e:
            self._logger.warning(f"⚠️ Ошибка навигации {url}: {e}")
            return False

    def _inject_adblocker(self):
        """CSS + JS блокировка рекламы"""
        css = """
        .ad-container, div[id^="ts_ad_"], .mn-related-container,
        .mn-container, .mn-outer, .mn-thumb, .ts-outstream-video,
        [class*="ad-"], [class*="advert"], [class*="sponsor"], [class*="promo"] {
            display: none !important; visibility: hidden !important;
            height: 0 !important; overflow: hidden !important;
        }
        [id*="ts_ad"], [id*="mn-thumb"] { display: none !important; }
        video[src*="tsyndicate"], video[src*="sacdnssedge"] { display: none !important; }
        """
        js = """
        window.NativeAd = function(){}; window.TSOutstreamVideo = function(){};
        window._TSFOOTER = function(){}; window._TSHEADER = function(){};
        const removeAds = () => {
            document.querySelectorAll('.ad-container, [id^="ts_ad_"], .mn-related-container, .ts-outstream-video')
                .forEach(el => { if (el.parentNode) el.parentNode.removeChild(el); });
        };
        removeAds(); setInterval(removeAds, 500);
        """
        try:
            self.page.add_style_tag(content=css)
            self.page.add_init_script(js)
        except:
            pass

    def stop(self) -> None:
        """Остановка"""
        try:
            if self.page: self.page.close()
            if self.context: self.context.close()
            if self.browser: self.browser.close()
            if self.playwright: self.playwright.stop()
        except:
            pass

    def search_creator(self, name: str, service: str = "patreon") -> List[Dict]:
        """🔍 Поиск создателя """
        if not self.page:
            return []
        
        results = []
        try:
            search_url = f"{self.BASE_URL}/artists?q={name.replace(' ', '%20')}"
            self._logger.info(f"🔍 Поиск: {search_url}")
            
            if not self._goto(search_url):
                return []
            
            try:
                self.page.wait_for_selector('a[href*="/user/"]', timeout=10000)
                time.sleep(1)  
            except:
                self._logger.warning("⚠️ Таймаут ожидания карточек, пробуем парсить как есть...")
          
            count = self.page.evaluate("""
                () => document.querySelectorAll('a[href*="/user/"]').length
            """)
            self._logger.info(f"📋 Найдено элементов на странице: {count}")
            
            creators = self.page.evaluate("""
                () => {
                    const creators = [];
               
                    const cards = document.querySelectorAll('a[href*="/user/"]');
                    
                    cards.forEach(card => {
                        const href = card.getAttribute('href');
                        if (!href) return;
                        
                 
                        const match = href.match(/\\/(patreon|fanbox|onlyfans|gumroad|subscribestar)\\/user\\/(\\d+)/);
                        if (!match) return;
                        
                        const service = match[1];
                        const creatorId = match[2];
                        
                        const nameEl = card.querySelector('.user-card__name, [class*="name"], .text-4xl, h1');
                        const creatorName = nameEl ? nameEl.textContent.trim() : 
                                           card.getAttribute('data-name') || 
                                           creatorId;
                        
                    
                        const exists = creators.find(c => c.creator_id === creatorId);
                        if (!exists) {
                            creators.push({
                                creator_id: creatorId, 
                                service: service,
                                name: creatorName,
                                url: href.startsWith('http') ? href : 'https://kemono.cr' + href
                            });
                        }
                    });
                    return creators;
                }
            """)
            
            self._logger.info(f"📦 Распознано создателей: {len(creators)}")
            
            for creator in creators:
                if name.lower() in creator.get("name", "").lower():
                    self._logger.info(f"✅ Совпадение: {creator['name']} (ID: {creator['creator_id']})")
                    results.append(creator)
            
            return results
            
        except Exception as e:
            self._logger.error(f"❌ Ошибка поиска: {e}", exc_info=True)

            try:
                with open("debug_search.html", "w", encoding="utf-8") as f:
                    f.write(self.page.content())
                self._logger.info("💾 HTML сохранён в debug_search.html")
            except:
                pass
            return []
        
    def crawl_creator(self, service: str, creator_id: str):

        posts = self.get_all_posts_paginated(service, creator_id)

        self._logger.info(f"Найдено постов: {len(posts)}")

        all_links = []

        for post in posts:

            links = self.extract_dropbox_links(
                service,
                creator_id,
                post["id"]
            )

            all_links.extend(links)

        return all_links

    def get_all_posts_paginated(self, service: str, creator_id: str, limit: int = 500) -> List[Dict]:
        """Получение постов с пагинацией"""
        if not self.page:
            return []
        
        all_posts = []
        offset = 0
        page_num = 1
        
        while len(all_posts) < limit:
            url = f"{self.BASE_URL}/{service}/user/{creator_id}?o={offset}" if offset > 0 else f"{self.BASE_URL}/{service}/user/{creator_id}"
            
            if not self._goto(url):
                break
            

                        
            posts = self.page.evaluate("""
                () => {
                    const posts = [];
                    const postElements = document.querySelectorAll('article.post-card');
                    
                    postElements.forEach(post => {
                        const link = post.querySelector('a[href*="/post/"]');
                        const href = link ? link.getAttribute('href') : '';
                        const postId = href.match(/\\/post\\/([0-9]+)/)?.[1];
                        
                        if (!postId) return;
                        
                        const titleEl = post.querySelector('.post-card__header, .post-card__title');
                        const dateEl = post.querySelector('time.timestamp');
                        
                        posts.push({
                            id: postId,
                            title: titleEl ? titleEl.textContent.trim() : 'No title',
                            published: dateEl ? dateEl.getAttribute('datetime') : null,
                            url: href.startsWith('http') ? href : 'https://kemono.cr' + href
                        });
                    });
                    
                    return posts;
                }
            """)
            
            if not posts:
                break
            
            all_posts.extend(posts)
            self._logger.info(f"📄 Стр. {page_num}: +{len(posts)} постов (всего: {len(all_posts)})")
            
        
            next_btn = self.page.query_selector('a.pagination-button-after-current, a[href*="?o="][href*=">"]')
            if not next_btn or len(all_posts) >= limit:
                break
            
            offset += 50
            page_num += 1
        
        return all_posts[:limit]
    
    def deduplicate_links(self, links: List[Dict]) -> List[Dict]:

        seen = set()
        result = []

        for link in links:

            url = link["url"]

            if url not in seen:
                seen.add(url)
                result.append(link)

        return result

    def extract_dropbox_links(
            self,
            service: str,
            creator_id: str,
            post_id: str,
            visited: Optional[Set[str]] = None
    ) -> List[Dict]:
        """Парсинг Dropbox ссылок из поста и связанных постов (BFS без рекурсии)"""

        if visited is None:
            visited = set()

        queue = [post_id]
        dropbox_links = []

        while queue:
            current_post = queue.pop(0)

            if current_post in visited:
                continue

            visited.add(current_post)

            try:
                url = f"{self.BASE_URL}/{service}/user/{creator_id}/post/{current_post}"

                if not self._goto(url):
                    continue

                # ждём загрузку поста
                self.page.wait_for_selector("div.post__content")

                # получаем title
                title = self.page.eval_on_selector(
                    "h1.post__title",
                    "el => el ? el.textContent.trim() : null"
                )

                # получаем все ссылки из поста
                links = self.page.eval_on_selector_all(
                    "div.post__content a[href]",
                    """els => els.map(e => ({
                        href: e.getAttribute('href'),
                        text: (e.textContent || '').trim()
                    }))"""
                )

                for link in links:
                    href = link["href"]
                    text = link["text"] or "Dropbox file"

                    if not href:
                        continue

                    href = unescape(href)

                    # -----------------------------
                    # Dropbox ссылки
                    # -----------------------------
                    if "dropbox.com" in href:

                        if href.startswith("/"):
                            href = "https://www.dropbox.com" + href

                        dropbox_links.append({
                            "url": href,
                            "text": text,
                            "post_id": current_post,
                            "creator_id": creator_id,
                            "service": service,
                            "title": title
                        })

                    # -----------------------------
                    # ссылка на другой пост
                    # -----------------------------
                    elif f"/{service}/post/" in href:

                        nested_post_id = (
                            href.split("/post/")[-1]
                            .split("/")[0]
                            .split("?")[0]
                        )

                        if nested_post_id.isdigit() and nested_post_id not in visited:
                            queue.append(nested_post_id)

            except Exception as e:
                self._logger.error(f"❌ Ошибка парсинга {current_post}: {e}")

        return dropbox_links

    def take_screenshot(self, save_path: str) -> bool:
        """Скриншот"""
        if not self.page:
            return False
        try:
            self.page.screenshot(path=save_path, full_page=True)
            return True
        except:
            return False


