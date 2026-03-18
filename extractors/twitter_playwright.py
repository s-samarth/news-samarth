"""
Twitter/X Extractor using Playwright for browser-based scraping.

This module provides strict session isolation using Playwright's persistent context,
ensuring the burner account's browser profile never contaminates the main browser.
"""

import asyncio
import os
import random
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional

from dotenv import load_dotenv
from playwright.async_api import async_playwright, BrowserContext, Page, TimeoutError as PlaywrightTimeout

from extractors.base import BaseExtractor

# Load environment variables
load_dotenv()


class TwitterPlaywrightExtractor(BaseExtractor):
    """
    Twitter/X extractor using Playwright with isolated browser session.
    
    Features:
    - Strict session isolation via persistent context
    - Automatic login with credential verification
    - Session persistence between runs
    - Human-like browsing behavior
    - Headless mode by default (toggle for debugging)
    """
    
    def __init__(self, headless: bool = True, max_tweets: int = 10):
        """
        Initialize the Twitter Playwright extractor.
        
        Args:
            headless: Run browser in headless mode (default True)
            max_tweets: Maximum number of tweets to extract per source
        """
        super().__init__()
        self.headless = headless
        self.max_tweets = max_tweets
        
        # Load credentials from environment
        self.username = os.getenv("TWITTER_USERNAME")
        self.password = os.getenv("TWITTER_PASSWORD")
        self.email = os.getenv("TWITTER_EMAIL")  # Optional, for verification
        
        # Profile directory for session persistence (isolated from system browser)
        self.profile_dir = Path(".playwright_twitter_profile")
        self.profile_dir.mkdir(exist_ok=True)
        
        # Validate credentials
        if not self.username or not self.password:
            raise ValueError(
                "Twitter credentials not found. Please set TWITTER_USERNAME and "
                "TWITTER_PASSWORD in your .env file."
            )
    
    async def _get_context(self, playwright) -> BrowserContext:
        """
        Create or launch a persistent browser context for strict session isolation.
        
        Returns:
            BrowserContext: Isolated browser context with saved session state
        """
        browser = await playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ]
        )
        
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
            locale="en-US",
            timezone_id="America/New_York",
        )
        
        # Add stealth scripts to avoid detection
        await context.add_init_script("""
            // Override navigator.webdriver
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Override chrome runtime
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };
            
            // Override permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)
        
        return context
    
    async def _is_authenticated(self, page: Page) -> bool:
        """
        Check if the current session is already authenticated.
        
        Args:
            page: Playwright page object
            
        Returns:
            bool: True if authenticated, False otherwise
        """
        try:
            # Navigate to home to check authentication status
            await page.goto("https://x.com/home", wait_until="networkidle", timeout=30000)
            await asyncio.sleep(random.uniform(1, 2))
            
            # Check if we're redirected to login page
            current_url = page.url
            if "/login" in current_url or "/i/flow/login" in current_url:
                return False
            
            # Check for presence of authenticated elements
            # Look for compose tweet button or profile menu
            compose_button = await page.query_selector('[data-testid="SideNav_NewTweet_Button"]')
            profile_link = await page.query_selector('[data-testid="AppTabBar_Profile_Link"]')
            
            return compose_button is not None or profile_link is not None
            
        except Exception as e:
            print(f"Error checking authentication: {e}")
            return False
    
    async def _login(self, page: Page) -> bool:
        """
        Handle the login flow with credential verification.
        
        Args:
            page: Playwright page object
            
        Returns:
            bool: True if login successful, False otherwise
        """
        try:
            print("Navigating to Twitter login page...")
            await page.goto("https://x.com/i/flow/login", wait_until="networkidle", timeout=60000)
            await asyncio.sleep(random.uniform(2, 4))
            
            # Step 1: Enter username
            print("Entering username...")
            username_input = await page.wait_for_selector(
                'input[autocomplete="username"]',
                timeout=30000
            )
            await username_input.click()
            await asyncio.sleep(random.uniform(0.3, 0.7))
            await username_input.fill(self.username)
            await asyncio.sleep(random.uniform(0.5, 1))
            
            # Click Next button
            next_button = await page.wait_for_selector(
                'div[role="button"]:has-text("Next")',
                timeout=10000
            )
            await next_button.click()
            await asyncio.sleep(random.uniform(2, 4))
            
            # Step 2: Handle potential email/phone verification
            # Twitter sometimes asks for email to verify unusual login
            try:
                verification_input = await page.wait_for_selector(
                    'input[data-testid="ocfEnterTextTextInput"]',
                    timeout=5000
                )
                if verification_input and self.email:
                    print("Email verification required, entering email...")
                    await verification_input.click()
                    await asyncio.sleep(random.uniform(0.3, 0.7))
                    await verification_input.fill(self.email)
                    await asyncio.sleep(random.uniform(0.5, 1))
                    
                    next_button = await page.wait_for_selector(
                        'div[role="button"]:has-text("Next")',
                        timeout=10000
                    )
                    await next_button.click()
                    await asyncio.sleep(random.uniform(2, 4))
                elif verification_input:
                    print("Email verification required but TWITTER_EMAIL not set!")
                    return False
            except PlaywrightTimeout:
                # No verification needed, continue
                pass
            
            # Step 3: Enter password
            print("Entering password...")
            password_input = await page.wait_for_selector(
                'input[name="password"]',
                timeout=30000
            )
            await password_input.click()
            await asyncio.sleep(random.uniform(0.3, 0.7))
            await password_input.fill(self.password)
            await asyncio.sleep(random.uniform(0.5, 1))
            
            # Click Login button
            login_button = await page.wait_for_selector(
                'div[data-testid="LoginForm_Login_Button"]',
                timeout=10000
            )
            await login_button.click()
            await asyncio.sleep(random.uniform(3, 5))
            
            # Step 4: Verify login success
            # Wait for redirect to home page
            await page.wait_for_url("**/home", timeout=30000)
            
            print("Login successful!")
            return True
            
        except PlaywrightTimeout as e:
            print(f"Login timeout: {e}")
            return False
        except Exception as e:
            print(f"Login error: {e}")
            return False
    
    async def _human_like_delay(self, min_seconds: float = 1, max_seconds: float = 3):
        """Add a random human-like delay."""
        await asyncio.sleep(random.uniform(min_seconds, max_seconds))
    
    async def _scroll_page(self, page: Page, scrolls: int = 3):
        """
        Scroll the page to trigger lazy loading of tweets.
        
        Args:
            page: Playwright page object
            scrolls: Number of scroll actions to perform
        """
        for i in range(scrolls):
            # Random scroll distance
            scroll_distance = random.randint(300, 800)
            await page.evaluate(f"window.scrollBy(0, {scroll_distance})")
            await self._human_like_delay(1.5, 3)
    
    async def _extract_tweets(self, page: Page, handle: str) -> List[Dict]:
        """
        Extract tweets from a user's profile page.
        
        Args:
            page: Playwright page object
            handle: Twitter handle to scrape
            
        Returns:
            List[Dict]: List of tweet data dictionaries
        """
        tweets = []
        
        try:
            # Navigate to user's profile
            profile_url = f"https://x.com/{handle}"
            print(f"Navigating to {profile_url}...")
            await page.goto(profile_url, wait_until="networkidle", timeout=60000)
            await self._human_like_delay(2, 4)
            
            # Scroll to load more tweets (more scrolls when targeting a specific date)
            scrolls = getattr(self, '_target_date_scrolls', None) or 3
            await self._scroll_page(page, scrolls=scrolls)
            
            # Find all tweet articles
            tweet_elements = await page.query_selector_all('article[data-testid="tweet"]')
            print(f"Found {len(tweet_elements)} tweet elements")
            
            for i, tweet_el in enumerate(tweet_elements):
                if len(tweets) >= self.max_tweets:
                    break
                
                try:
                    tweet_data = await self._parse_tweet_element(tweet_el, handle)
                    if tweet_data:
                        tweets.append(tweet_data)
                except Exception as e:
                    print(f"Error parsing tweet {i}: {e}")
                    continue
            
            print(f"Successfully extracted {len(tweets)} tweets")
            return tweets
            
        except Exception as e:
            print(f"Error extracting tweets: {e}")
            return tweets
    
    async def _parse_tweet_element(self, tweet_el, handle: str) -> Optional[Dict]:
        """
        Parse a single tweet element to extract data.
        
        Args:
            tweet_el: Playwright element handle for the tweet
            handle: Twitter handle being scraped
            
        Returns:
            Dict: Tweet data or None if parsing fails
        """
        try:
            # Extract tweet text
            text_el = await tweet_el.query_selector('[data-testid="tweetText"]')
            content_text = ""
            if text_el:
                content_text = await text_el.inner_text()
            
            # Extract tweet URL and timestamp
            time_el = await tweet_el.query_selector('time')
            tweet_url = ""
            timestamp = ""
            if time_el:
                # Get timestamp from datetime attribute
                timestamp = await time_el.get_attribute("datetime")
                
                # Get URL from parent link
                parent_link = await time_el.evaluate_handle("el => el.closest('a')")
                if parent_link:
                    href = await parent_link.get_attribute("href")
                    if href:
                        tweet_url = f"https://x.com{href}"
            
            # Check if it's a retweet
            is_retweet = False
            social_context = await tweet_el.query_selector('[data-testid="socialContext"]')
            if social_context:
                context_text = await social_context.inner_text()
                is_retweet = "retweeted" in context_text.lower()
            
            # Also check for retweet indicator
            retweet_indicator = await tweet_el.query_selector('span:has-text("Retweeted")')
            if retweet_indicator:
                is_retweet = True
            
            # Extract media link if present
            media_link = None
            media_el = await tweet_el.query_selector('[data-testid="tweetPhoto"] img, [data-testid="tweetVideo"] img')
            if media_el:
                media_link = await media_el.get_attribute("src")
            
            # Build title from first 100 chars of content
            title = f"Tweet by @{handle}"
            if content_text:
                title_preview = content_text[:100].replace("\n", " ").strip()
                if len(content_text) > 100:
                    title_preview += "..."
                title = title_preview
            
            # Format timestamp to ISO 8601 if available
            if timestamp:
                try:
                    # Twitter provides ISO format already
                    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    timestamp = dt.isoformat()
                except:
                    pass
            
            return {
                "platform": "twitter",
                "source_name": f"@{handle}",
                "title": title,
                "content_text": content_text,
                "url": tweet_url,
                "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
                "media_link": media_link,
                "is_retweet": is_retweet,
            }
            
        except Exception as e:
            print(f"Error parsing tweet element: {e}")
            return None
    
    async def _extract_async(self, sources: List[Dict]) -> List[Dict]:
        """
        Async extraction method that handles browser automation.
        
        Args:
            sources: List of source configurations from sources.json
            
        Returns:
            List[Dict]: List of extracted tweet data
        """
        all_tweets = []
        
        async with async_playwright() as playwright:
            context = await self._get_context(playwright)
            page = await context.new_page()
            
            try:
                # Check authentication and login if needed
                is_authenticated = await self._is_authenticated(page)
                
                if not is_authenticated:
                    print("Not authenticated, attempting login...")
                    login_success = await self._login(page)
                    if not login_success:
                        print("Login failed! Cannot extract tweets.")
                        return []
                else:
                    print("Already authenticated, proceeding with extraction...")
                
                # Extract tweets from each source
                for source in sources:
                    handle = source.get("handle", "")
                    if not handle:
                        print(f"Skipping source with no handle: {source}")
                        continue
                    
                    max_tweets = source.get("max_tweets", self.max_tweets)
                    self.max_tweets = max_tweets
                    
                    print(f"Extracting tweets from @{handle}...")
                    tweets = await self._extract_tweets(page, handle)
                    all_tweets.extend(tweets)
                    
                    # Delay between different profiles
                    await self._human_like_delay(3, 6)
                
            except Exception as e:
                print(f"Extraction error: {e}")
                raise
            finally:
                # Always close the context cleanly
                await context.close()
        
        return all_tweets
    
    def _filter_by_date(self, tweets: List[Dict], target_date: Optional[str] = None) -> List[Dict]:
        """
        Filter tweets by target date.
        
        Args:
            tweets: List of tweet dictionaries
            target_date: Optional date string (YYYY-MM-DD) to filter by
            
        Returns:
            List[Dict]: Filtered list of tweets
        """
        if not target_date:
            return tweets
        
        filtered_tweets = []
        for tweet in tweets:
            tweet_timestamp = tweet.get("timestamp", "")
            if tweet_timestamp:
                try:
                    # Parse the timestamp and extract date
                    dt = datetime.fromisoformat(tweet_timestamp.replace("Z", "+00:00"))
                    tweet_date = dt.strftime("%Y-%m-%d")
                    if tweet_date == target_date:
                        filtered_tweets.append(tweet)
                except:
                    # If parsing fails, include the tweet
                    filtered_tweets.append(tweet)
            else:
                # If no timestamp, include the tweet
                filtered_tweets.append(tweet)
        
        return filtered_tweets

    def extract(self, sources: List[Dict], target_date: Optional[str] = None) -> List[Dict]:
        """
        Extract tweets from Twitter/X profiles.

        This is the main entry point matching the BaseExtractor interface.
        It runs the async extraction in an event loop.

        Args:
            sources: List of source configurations from sources.json
            target_date: Optional date string (YYYY-MM-DD) to filter tweets by date

        Returns:
            List[Dict]: List of extracted tweet data formatted for ChromaDB
        """
        # When targeting a specific date, increase scroll count for more tweets
        if target_date:
            self._target_date_scrolls = 6
        else:
            self._target_date_scrolls = None

        tweets = asyncio.run(self._extract_async(sources))
        return self._filter_by_date(tweets, target_date)
