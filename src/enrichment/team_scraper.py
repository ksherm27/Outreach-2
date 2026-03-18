from __future__ import annotations

import re
from dataclasses import dataclass

import httpx
from bs4 import BeautifulSoup

from src.shared.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ContactCandidate:
    name: str
    title: str | None = None
    email: str | None = None
    linkedin_url: str | None = None
    confidence: float = 0.0


class TeamPageScraper:
    """Scrapes company /about and /team pages for contact information."""

    TEAM_PATHS = [
        "/about",
        "/team",
        "/about-us",
        "/our-team",
        "/leadership",
        "/about/team",
        "/company",
        "/company/team",
    ]

    EMAIL_PATTERN = re.compile(
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    )
    LINKEDIN_PATTERN = re.compile(
        r"https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+"
    )

    def scrape(self, domain: str) -> list[ContactCandidate]:
        """Try common team page paths and extract contact information."""
        candidates: list[ContactCandidate] = []

        with httpx.Client(timeout=15, follow_redirects=True) as client:
            for path in self.TEAM_PATHS:
                url = f"https://{domain}{path}"
                try:
                    response = client.get(
                        url,
                        headers={
                            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
                        },
                    )
                    if response.status_code != 200:
                        continue

                    page_candidates = self._extract_contacts(response.text, domain)
                    candidates.extend(page_candidates)

                except Exception:
                    continue

        # Deduplicate by name
        seen_names: set[str] = set()
        unique: list[ContactCandidate] = []
        for c in candidates:
            if c.name.lower() not in seen_names:
                seen_names.add(c.name.lower())
                unique.append(c)

        logger.info("team_page_scraped", domain=domain, contacts_found=len(unique))
        return unique

    def _extract_contacts(self, html: str, domain: str) -> list[ContactCandidate]:
        """Extract contact candidates from HTML."""
        soup = BeautifulSoup(html, "lxml")
        candidates: list[ContactCandidate] = []

        # Look for team member cards/sections
        team_sections = soup.select(
            ".team-member, .person, .member, .staff, .bio, "
            "[class*='team'], [class*='person'], [class*='member']"
        )

        for section in team_sections:
            name = self._extract_name(section)
            if not name:
                continue

            title = self._extract_title(section)
            email = self._extract_email(section)
            linkedin = self._extract_linkedin(section)

            confidence = 0.3  # Base confidence for finding on team page
            if title:
                confidence += 0.2
            if email:
                confidence += 0.3
            if linkedin:
                confidence += 0.2

            candidates.append(ContactCandidate(
                name=name,
                title=title,
                email=email,
                linkedin_url=linkedin,
                confidence=min(1.0, confidence),
            ))

        # Also scan full page for emails
        all_emails = self.EMAIL_PATTERN.findall(str(soup))
        all_linkedins = self.LINKEDIN_PATTERN.findall(str(soup))

        # Filter out generic emails
        generic = {"info@", "hello@", "contact@", "support@", "sales@", "hr@", "careers@"}
        personal_emails = [
            e for e in all_emails
            if not any(e.lower().startswith(g) for g in generic)
            and domain.lower() in e.lower()
        ]

        return candidates

    def _extract_name(self, section) -> str | None:
        """Extract a person's name from a team member section."""
        name_selectors = ["h2", "h3", "h4", ".name", "[class*='name']", "strong"]
        for selector in name_selectors:
            el = section.select_one(selector)
            if el:
                text = el.get_text(strip=True)
                # Basic validation: should look like a name (2-4 words, no digits)
                words = text.split()
                if 2 <= len(words) <= 4 and not any(c.isdigit() for c in text):
                    return text
        return None

    def _extract_title(self, section) -> str | None:
        """Extract a job title from a team member section."""
        title_selectors = [
            ".title", ".role", ".position", ".job-title",
            "[class*='title']", "[class*='role']", "[class*='position']",
            "p", "span",
        ]
        for selector in title_selectors:
            els = section.select(selector)
            for el in els:
                text = el.get_text(strip=True)
                title_keywords = [
                    "VP", "Director", "Head", "Chief", "Manager",
                    "Officer", "President", "Lead", "CRO", "CMO", "CEO",
                ]
                if any(kw.lower() in text.lower() for kw in title_keywords):
                    return text
        return None

    def _extract_email(self, section) -> str | None:
        """Extract an email from a team member section."""
        # Check mailto links
        mailto = section.select_one("a[href^='mailto:']")
        if mailto:
            return mailto["href"].replace("mailto:", "").split("?")[0]

        # Regex scan
        match = self.EMAIL_PATTERN.search(str(section))
        return match.group(0) if match else None

    def _extract_linkedin(self, section) -> str | None:
        """Extract a LinkedIn URL from a team member section."""
        linkedin_link = section.select_one("a[href*='linkedin.com/in/']")
        if linkedin_link:
            return linkedin_link["href"]

        match = self.LINKEDIN_PATTERN.search(str(section))
        return match.group(0) if match else None
