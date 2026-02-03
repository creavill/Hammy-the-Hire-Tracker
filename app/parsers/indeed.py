"""
Indeed Parser - Extract jobs from Indeed job alert emails
"""

import re
import logging
from bs4 import BeautifulSoup
from .base import BaseParser

logger = logging.getLogger(__name__)


class IndeedParser(BaseParser):
    """Parser for Indeed job alert emails."""

    @property
    def source_name(self) -> str:
        return 'indeed'

    def parse(self, html: str, email_date: str) -> list:
        """
        Extract job listings from Indeed job alert emails.

        Args:
            html: Raw HTML content from Indeed email
            email_date: ISO format date string when email was received

        Returns:
            List of job dictionaries
        """
        jobs = []
        soup = BeautifulSoup(html, 'html.parser')

        # Indeed uses table cells or divs for job cards
        job_links = soup.find_all('a', href=re.compile(r'indeed\.com.*(jk=|vjk=)[a-f0-9]+'))

        exclude_keywords = ['unsubscribe', 'help', 'view all', 'see all', 'homepage',
                           'messages', 'notifications', 'easily apply', 'responsive employer']

        seen = set()
        for link in job_links:
            url = self.clean_job_url(link.get('href', ''))
            if not url or url in seen:
                continue

            full_text = link.get_text(separator=' ', strip=True)
            full_text = ' '.join(full_text.split())

            if any(keyword in full_text.lower() for keyword in exclude_keywords):
                continue

            if not full_text or len(full_text) < 5:
                continue

            seen.add(url)

            title = full_text
            company = ""
            location = ""

            # Find parent container
            parent = link.find_parent(['td', 'div', 'li'])
            raw_text = full_text

            if parent:
                text = parent.get_text('\n', strip=True)
                lines = [l.strip() for l in text.split('\n') if l.strip() and len(l.strip()) > 2]

                # Indeed format: Title / Company / Location / Salary / Description
                for i, line in enumerate(lines):
                    # Skip rating lines
                    if re.match(r'^\d+\.?\d*\s*\d', line):
                        continue

                    if title in line and i + 1 < len(lines):
                        for j in range(i + 1, min(i + 4, len(lines))):
                            potential_company = lines[j]
                            if not re.match(r'^\d+\.?\d*\s*\d', potential_company) and '$' not in potential_company:
                                company = potential_company[:100]

                                for k in range(j + 1, min(j + 3, len(lines))):
                                    potential_location = lines[k]
                                    if ('remote' in potential_location.lower() or
                                        ',' in potential_location or
                                        any(state in potential_location for state in ['CA', 'NY', 'TX', 'FL'])):
                                        location = potential_location[:100]
                                        break
                                break
                        break

                raw_text = ' '.join(lines[:6])[:1000]

            title = self.clean_text_field(title)
            company = self.clean_text_field(company) if company else "Unknown"
            location = self.clean_text_field(location)

            jobs.append({
                'job_id': self.generate_job_id(url, title, company),
                'title': title[:200],
                'company': company[:100],
                'location': location[:100],
                'url': url,
                'source': self.source_name,
                'raw_text': raw_text,
                'created_at': email_date,
                'email_date': email_date
            })

        return jobs
