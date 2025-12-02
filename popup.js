const API_URL = 'http://localhost:5000/api/capture';

// Get current tab URL on load
chrome.tabs.query({active: true, currentWindow: true}, (tabs) => {
  if (tabs[0]) {
    document.getElementById('url').value = tabs[0].url;
    
    // Try to auto-fill title from page title
    let title = tabs[0].title || '';
    
    // Clean up common patterns
    title = title
      .replace(/\| LinkedIn$/, '')
      .replace(/- Indeed\.com$/, '')
      .replace(/\| Glassdoor$/, '')
      .replace(/at .* \| .*$/, '')  // "Job at Company | Site"
      .trim();
    
    document.getElementById('title').value = title;
  }
});

// Extract content from page
document.getElementById('extractBtn').addEventListener('click', async () => {
  const btn = document.getElementById('extractBtn');
  btn.disabled = true;
  btn.textContent = 'Extracting...';
  
  try {
    const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
    
    const results = await chrome.scripting.executeScript({
      target: {tabId: tab.id},
      func: extractJobData
    });
    
    if (results && results[0] && results[0].result) {
      const data = results[0].result;
      
      if (data.title) document.getElementById('title').value = data.title;
      if (data.company) document.getElementById('company').value = data.company;
      if (data.location) document.getElementById('location').value = data.location;
      if (data.description) document.getElementById('description').value = data.description;
      
      showStatus('Extracted! Review and save.', 'success');
    }
  } catch (err) {
    console.error(err);
    showStatus('Extraction failed. Fill manually.', 'error');
  }
  
  btn.disabled = false;
  btn.textContent = '🔍 Extract from Page';
});

// Content script function - runs in page context
function extractJobData() {
  const data = {
    title: '',
    company: '',
    location: '',
    description: ''
  };
  
  const url = window.location.href;
  
  // LinkedIn
  if (url.includes('linkedin.com')) {
    data.title = document.querySelector('h1.t-24, h1.topcard__title, .job-details-jobs-unified-top-card__job-title')?.innerText?.trim() || '';
    data.company = document.querySelector('a.topcard__org-name-link, .job-details-jobs-unified-top-card__company-name')?.innerText?.trim() || '';
    data.location = document.querySelector('.topcard__flavor--bullet, .job-details-jobs-unified-top-card__bullet')?.innerText?.trim() || '';
    data.description = document.querySelector('.description__text, .jobs-description__content')?.innerText?.trim() || '';
  }
  
  // Indeed
  else if (url.includes('indeed.com')) {
    data.title = document.querySelector('h1.jobsearch-JobInfoHeader-title, [data-testid="jobsearch-JobInfoHeader-title"]')?.innerText?.trim() || '';
    data.company = document.querySelector('[data-testid="inlineHeader-companyName"], .jobsearch-InlineCompanyRating-companyHeader')?.innerText?.trim() || '';
    data.location = document.querySelector('[data-testid="job-location"], .jobsearch-JobInfoHeader-subtitle > div:last-child')?.innerText?.trim() || '';
    data.description = document.querySelector('#jobDescriptionText, .jobsearch-jobDescriptionText')?.innerText?.trim() || '';
  }
  
  // WeWorkRemotely
  else if (url.includes('weworkremotely.com')) {
    data.title = document.querySelector('h1.listing-header-container')?.innerText?.trim() || '';
    data.company = document.querySelector('.company-card h2, .listing-header-container + h2')?.innerText?.trim() || '';
    data.location = 'Remote';
    data.description = document.querySelector('.listing-container')?.innerText?.trim() || '';
  }
  
  // Greenhouse
  else if (url.includes('greenhouse.io') || url.includes('boards.greenhouse.io')) {
    data.title = document.querySelector('h1.app-title, .job-title')?.innerText?.trim() || '';
    data.company = document.querySelector('.company-name')?.innerText?.trim() || '';
    data.location = document.querySelector('.location')?.innerText?.trim() || '';
    data.description = document.querySelector('#content, .job-description')?.innerText?.trim() || '';
  }
  
  // Lever
  else if (url.includes('lever.co') || url.includes('jobs.lever.co')) {
    data.title = document.querySelector('h2.posting-headline, .posting-title')?.innerText?.trim() || '';
    data.company = document.querySelector('.main-header-logo img')?.alt || '';
    data.location = document.querySelector('.posting-categories .location, .workplaceTypes')?.innerText?.trim() || '';
    data.description = document.querySelector('.posting-page .content, [data-qa="job-description"]')?.innerText?.trim() || '';
  }
  
  // Glassdoor
  else if (url.includes('glassdoor.com')) {
    data.title = document.querySelector('[data-test="job-title"], .job-title')?.innerText?.trim() || '';
    data.company = document.querySelector('[data-test="employer-name"], .employer-name')?.innerText?.trim() || '';
    data.location = document.querySelector('[data-test="location"], .location')?.innerText?.trim() || '';
    data.description = document.querySelector('.jobDescriptionContent, .desc')?.innerText?.trim() || '';
  }
  
  // Wellfound (AngelList)
  else if (url.includes('wellfound.com') || url.includes('angel.co')) {
    data.title = document.querySelector('h1[class*="jobTitle"], h1[class*="title"], .job-title h1')?.innerText?.trim() || '';
    data.company = document.querySelector('a[class*="company"], h2[class*="company"], .company-name')?.innerText?.trim() || '';
    data.location = document.querySelector('[class*="location"], .job-location')?.innerText?.trim() || '';
    data.description = document.querySelector('[class*="description"], .job-description, [class*="jobDescription"]')?.innerText?.trim() || '';
  }
  
  // Generic fallback
  else {
    // Try common selectors
    data.title = document.querySelector('h1')?.innerText?.trim() || document.title || '';
    data.description = document.querySelector('[class*="description"], [class*="content"], article, main')?.innerText?.trim() || '';
    
    // Limit description length
    if (data.description.length > 5000) {
      data.description = data.description.substring(0, 5000) + '...';
    }
  }
  
  return data;
}

// Save to Job Tracker
document.getElementById('captureBtn').addEventListener('click', async () => {
  const title = document.getElementById('title').value.trim();
  const company = document.getElementById('company').value.trim();
  const location = document.getElementById('location').value.trim();
  const url = document.getElementById('url').value.trim();
  const description = document.getElementById('description').value.trim();
  
  if (!title) {
    showStatus('Title is required', 'error');
    return;
  }
  
  const btn = document.getElementById('captureBtn');
  btn.disabled = true;
  btn.textContent = 'Saving...';
  
  try {
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({title, company, location, url, description})
    });
    
    if (!response.ok) throw new Error('Server error');
    
    const result = await response.json();
    showStatus(`Saved! (${result.status})`, 'success');
    
    // Clear form after success
    setTimeout(() => window.close(), 1500);
    
  } catch (err) {
    console.error(err);
    showStatus('Failed to save. Is Job Tracker running on localhost:5000?', 'error');
  }
  
  btn.disabled = false;
  btn.textContent = '💾 Save to Job Tracker';
});

function showStatus(message, type) {
  const status = document.getElementById('status');
  status.textContent = message;
  status.className = 'status ' + type;
}
