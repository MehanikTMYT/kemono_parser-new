def check_ip(self) -> Dict[str, Any]:
        """Проверка IP с фолбэками"""
        services = [
            "https://ipapi.co/json/",
            "https://ipwho.is/",
            "https://ip-api.com/json/",
        ]
        
        for url in services:
            try:
                response = requests.get(url, timeout=8)
                data = response.json()
                
                if "country_code" in data:
                    country = data["country_code"]
                elif "country" in data:
                    country = data["country"]
                else:
                    continue
                    
                ip = data.get("ip", "Unknown")
                city = data.get("city", data.get("region", "Unknown"))
                is_russia = country.upper() == "RU"
                
                self._logger.info(f"📍 IP: {ip} | Страна: {country} | Город: {city}")
                if is_russia:
                    self._logger.warning("⚠️ РФ обнаружен! Включите VPN")
                return {"ip": ip, "country": country, "city": city, "is_russia": is_russia}
                
            except Exception as e:
                self._logger.debug(f"⚠️ Не удалось проверить через {url}: {e}")
                continue
        
        self._logger.warning("⚠️ Не удалось определить местоположение, продолжаем без проверки")
        return {"ip": "Unknown", "country": "Unknown", "city": "Unknown", "is_russia": False}