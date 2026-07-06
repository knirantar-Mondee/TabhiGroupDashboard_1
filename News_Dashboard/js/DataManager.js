export class DataManager {
  constructor() {
    this.brands = ['mondee', 'miraee', 'abhee'];
    this.data = {};
    this.brandVideoData = {};
  }
  
  async loadAllBrandsData() {
    for (const brand of this.brands) {
      this.data[brand] = await this.loadBrandExcel(brand);
    }
  }
  
  async loadBrandExcel(brandId) {
    const filenameMap = {
      mondee: 'raw_news_database_Mondee.xlsx',
      miraee: 'raw_news_database_Miraee.xlsx',
      abhee: 'raw_news_database_Abhee.xlsx'
    };
    
    const url = `./data/${filenameMap[brandId]}`;
    
    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`Failed to fetch ${url}`);
      }
      const arrayBuffer = await response.arrayBuffer();
      const data = new Uint8Array(arrayBuffer);
      const workbook = XLSX.read(data, { type: 'array' });
      
      const sheetName = workbook.SheetNames.includes("Raw_News") ? "Raw_News" : workbook.SheetNames[0];
      const worksheet = workbook.Sheets[sheetName];
      const jsonData = XLSX.utils.sheet_to_json(worksheet);
      
      return this.transformRowsToDashboardData(brandId, jsonData);
    } catch (err) {
      console.error(`Error loading database for brand ${brandId}:`, err);
      // Return a structured empty dataset so the UI doesn't crash
      return this.getEmptyBrandDataset(brandId);
    }
  }
  
  transformRowsToDashboardData(brandId, rows) {
    // Sort rows by Criticality_Score descending, then by Published_Date descending
    rows.sort((a, b) => {
      const scoreA = Number(a.Criticality_Score) || 0;
      const scoreB = Number(b.Criticality_Score) || 0;
      if (scoreB !== scoreA) {
        return scoreB - scoreA;
      }
      const dateA = a.Published_Date ? new Date(a.Published_Date) : new Date(0);
      const dateB = b.Published_Date ? new Date(b.Published_Date) : new Date(0);
      return dateB - dateA;
    });
    
    // Client-side deduplication to ensure unique entries in the UI
    const uniqueRows = [];
    const seenUrls = new Set();
    const seenTitles = new Set();
    
    rows.forEach(r => {
      const rawUrl = r.Article_URL ? r.Article_URL.trim().toLowerCase() : "";
      const rawTitle = r.Title ? r.Title.trim().toLowerCase() : "";
      
      let normUrl = rawUrl;
      try {
        const urlObj = new URL(rawUrl);
        normUrl = urlObj.origin + urlObj.pathname.replace(/\/$/, "");
      } catch(e) {}
      
      if (normUrl && seenUrls.has(normUrl)) return;
      if (rawTitle && seenTitles.has(rawTitle)) return;
      
      if (normUrl) seenUrls.add(normUrl);
      if (rawTitle) seenTitles.add(rawTitle);
      uniqueRows.push(r);
    });
    
    rows = uniqueRows;
    
    // 1. Core titles and texts based on brand
    const metaMap = {
      mondee: {
        title: "Mondee (B2B)",
        label: "MONDEE B2B LIVE ALERTS",
        headerBadge: "B2B RADAR",
        heroTitle: "B2B Distribution & Agency Intelligence",
        heroDesc: "GDS, wholesale consolidators, agency OTAs, and direct supplier portals competing with Mondee",
        footerLeft: "TABHI · Mondee B2B Intelligence Command Center · All sources public"
      },
      miraee: {
        title: "Miraee (B2E)",
        label: "MIRAEE B2E LIVE ALERTS",
        headerBadge: "B2E RADAR",
        heroTitle: "B2E Corporate & Expense Intelligence",
        heroDesc: "Corporate travel management platforms, corporate cards, and expense suites competing with Miraee",
        footerLeft: "TABHI · Miraee B2E Intelligence Command Center · All sources public"
      },
      abhee: {
        title: "Abhee (B2C)",
        label: "ABHEE B2C LIVE ALERTS",
        headerBadge: "B2C RADAR",
        heroTitle: "B2C Consumer Travel & OTA Intelligence",
        heroDesc: "Online Travel Agencies, vacation rental apps, and digital itinerary planners competing with Abhee",
        footerLeft: "TABHI · Abhee B2C Intelligence Command Center · All sources public"
      }
    };
    
    const brandMeta = metaMap[brandId] || metaMap.mondee;
    
    // 2. Count metrics
    const totalSignals = rows.length;
    const highThreatCount = rows.filter(r => r.Threat_Level === 'High').length;
    const mediumThreatCount = rows.filter(r => r.Threat_Level === 'Medium').length;
    const lowThreatCount = rows.filter(r => r.Threat_Level === 'Low' || !r.Threat_Level).length;
    
    // Get top topic (most frequent)
    const topicCounts = {};
    rows.forEach(r => {
      const t = r.Topic || 'General Travel News';
      topicCounts[t] = (topicCounts[t] || 0) + 1;
    });
    let topTheme = 'General Travel News';
    let maxTopicCount = 0;
    for (const [topic, count] of Object.entries(topicCounts)) {
      if (count > maxTopicCount) {
        maxTopicCount = count;
        topTheme = topic;
      }
    }
    
    // Get sentiment summary
    const sentiments = rows.map(r => r.Sentiment || 'Neutral');
    const posCount = sentiments.filter(s => s === 'Positive').length;
    const negCount = sentiments.filter(s => s === 'Negative').length;
    const posPercent = totalSignals > 0 ? Math.round((posCount / totalSignals) * 100) : 0;
    const negPercent = totalSignals > 0 ? Math.round((negCount / totalSignals) * 100) : 0;
    
    // 3. Stats Strip Data
    const stats = {
      'overview': [
        { label: "Total Signals Ingested", value: totalSignals.toString(), change: totalSignals > 0 ? `↑ ${rows.filter(r => this.isToday(r.Scrape_Date)).length}` : '', sub: "Deduplicated alerts" },
        { label: "High Threat Levels", value: highThreatCount.toString(), change: "", sub: "Requires immediate attention" },
        { label: "Medium Threat Levels", value: mediumThreatCount.toString(), change: "", sub: "Strategic movements" },
        { label: "Top Strategic Theme", value: topTheme, change: "", sub: "Dominant discussion topic" }
      ],
      'growth-marketing': [
        { label: "Partnerships Tracked", value: rows.filter(r => r.Topic === 'Partnership').length.toString(), change: "", sub: "Joint venture & alliance moves" },
        { label: "M&A Activity", value: rows.filter(r => r.Topic === 'M&A').length.toString(), change: "", sub: "Acquisitions & consolidations" },
        { label: "Positive Sentiment Impact", value: `${posPercent}%`, change: "", sub: "High positive competitor press" },
        { label: "Negative Sentiment Vulnerability", value: `${negPercent}%`, change: "", sub: "Under-performing competitors" }
      ],
      'product-strategy': [
        { label: "Product Launches", value: rows.filter(r => r.Topic === 'Product Launch').length.toString(), change: "", sub: "Digital features & API releases" },
        { label: "Restructuring Moves", value: rows.filter(r => r.Topic === 'Restructuring & Finance').length.toString(), change: "", sub: "Liquidity & corporate stress" },
        { label: "Low Threat Alerts", value: lowThreatCount.toString(), change: "", sub: "Standard industry updates" },
        { label: "Dominant Market Outlook", value: posCount >= negCount ? "Positive Growth" : "Market Correction", change: "", sub: "Overall sentiment direction" }
      ]
    };
    
    // 4. Build Ticker items
    const ticker = rows.slice(0, 5).map(r => ({
      tag: (r.Competitor || 'Market').toUpperCase().split(',')[0].trim(),
      text: r.Title,
      isHighlight: r.Threat_Level === 'High'
    }));
    if (ticker.length === 0) {
      ticker.push({ tag: "PIPELINE", text: "No active news articles scraped in the last 24 hours.", isHighlight: false });
    }
    
    // 5. Build Tab Columns
    const highCards = rows.filter(r => r.Threat_Level === 'High').map(r => this.mapRowToCard(r));
    const mediumCards = rows.filter(r => r.Threat_Level === 'Medium').map(r => this.mapRowToCard(r));
    const lowCards = rows.filter(r => r.Threat_Level === 'Low' || !r.Threat_Level).map(r => this.mapRowToCard(r));
    
    const overviewCols = [
      {
        title: "Critical Threats & Action",
        subtitle: "High priority risk factors",
        icon: "🚨",
        count: `${highCards.length} ALERTS`,
        banner: highCards.length > 0 ? `<strong>Watch Out:</strong> ${highCards[0].company} executed a high-threat movement: ${highCards[0].title}` : "No high-threat activities detected in this run.",
        cards: highCards
      },
      {
        title: "Competitor Movement",
        subtitle: "Medium threat strategic shifts",
        icon: "🛫",
        count: `${mediumCards.length} SCANNED`,
        banner: mediumCards.length > 0 ? `<strong>Update:</strong> ${mediumCards[0].company} is active on ${mediumCards[0].tags[0] || 'General'}.` : "No moderate threat activities detected.",
        cards: mediumCards
      },
      {
        title: "Market Activity",
        subtitle: "Low priority developments",
        icon: "🔧",
        count: `${lowCards.length} TRACKED`,
        banner: lowCards.length > 0 ? "General industry updates and minor releases." : "No low-threat news items cataloged.",
        cards: lowCards
      }
    ];
    
    // Growth tab
    const growth1Cards = rows.filter(r => ['M&A', 'Funding', 'Restructuring & Finance'].includes(r.Topic)).map(r => this.mapRowToCard(r));
    const growth2Cards = rows.filter(r => ['Partnership', 'Regulatory & Legal', 'Executive Move'].includes(r.Topic)).map(r => this.mapRowToCard(r));
    
    const growthCols = [
      {
        title: "Funding & Corporate Restructure",
        subtitle: "Investments, capital & debt updates",
        icon: "📈",
        count: `${growth1Cards.length} ITEMS`,
        banner: growth1Cards.length > 0 ? `<strong>Corporate Shift:</strong> Capital flows are shifting around B2B/B2C segments.` : "No major investments or financial updates.",
        cards: growth1Cards
      },
      {
        title: "Alliances & Executive Transitions",
        subtitle: "Partnerships & leadership moves",
        icon: "📢",
        count: `${growth2Cards.length} ITEMS`,
        banner: growth2Cards.length > 0 ? `<strong>Growth Playbook:</strong> Competitors are executing joint ventures.` : "No major partnerships reported in this cycle.",
        cards: growth2Cards
      }
    ];
    
    // Product Strategy tab
    const prod1Cards = rows.filter(r => r.Topic === 'Product Launch').map(r => this.mapRowToCard(r));
    const prod2Cards = rows.filter(r => ['General Travel News', 'General Industry News', 'General'].includes(r.Topic) || !r.Topic).map(r => this.mapRowToCard(r));
    
    const productCols = [
      {
        title: "Feature Releases & Tech Launches",
        subtitle: "API enhancements & UX deployments",
        icon: "⚙️",
        count: `${prod1Cards.length} LAUNCHES`,
        banner: prod1Cards.length > 0 ? `<strong>Technical Watch:</strong> Competitive feature velocity is active.` : "No digital releases or API changes detected.",
        cards: prod1Cards
      },
      {
        title: "General Sector Intelligence",
        subtitle: "Travel industry updates",
        icon: "🌐",
        count: `${prod2Cards.length} UPDATES`,
        banner: prod2Cards.length > 0 ? "Standard market changes and news summaries." : "No general sector updates.",
        cards: prod2Cards
      }
    ];
    
    // 6. Dynamic Insights bullet points
    const overviewInsights = rows.slice(0, 3).map(r => {
      return `<strong>${(r.Competitor || 'Competitor').split(',')[0].trim()}:</strong> ${r.Strategic_Implication || r.Competitor_Action || r.Title}`;
    });
    if (overviewInsights.length === 0) {
      overviewInsights.push("No strategic insights available in this dataset. Run scraper to pull updates.");
    }
    
    const growthInsights = rows.filter(r => ['M&A', 'Partnership', 'Funding'].includes(r.Topic)).slice(0, 2).map(r => {
      return `<strong>${r.Competitor}:</strong> ${r.Strategic_Implication || r.Title}`;
    });
    if (growthInsights.length === 0) {
      growthInsights.push("Standard corporate volumes recorded. No high impact alliances reported.");
    }
    
    const productInsights = rows.filter(r => r.Topic === 'Product Launch').slice(0, 2).map(r => {
      return `<strong>${r.Competitor}:</strong> ${r.Competitor_Action || r.Title}`;
    });
    if (productInsights.length === 0) {
      productInsights.push("Feature release velocity is normal. Track digital updates.");
    }
    
    const insights = {
      overview: overviewInsights,
      'growth-marketing': growthInsights,
      'product-strategy': productInsights
    };
    
    // 7. Video Briefs / Keynotes (filter for keynotes, interviews, calls, or video links)
    let videoArticles = rows.filter(r => {
      const title = (r.Title || '').toLowerCase();
      const url = (r.Article_URL || '').toLowerCase();
      const body = (r.News_Body || '').toLowerCase();
      const topic = (r.Topic || '').toLowerCase();
      
      return title.includes('keynote') || title.includes('interview') || title.includes('presentation') || 
             title.includes('earnings call') || title.includes('podcast') || title.includes('cxo') ||
             url.includes('youtube.com') || url.includes('/video/') || url.includes('vimeo.com') ||
             topic.includes('executive');
    }).slice(0, 3);
    
    // Fallback to high/medium threat strategic briefs if no specific keynotes are found
    if (videoArticles.length === 0) {
      videoArticles = rows.filter(r => r.Threat_Level === 'High' || r.Threat_Level === 'Medium').slice(0, 3);
    }
    
    const videos = [];
    const brandVideoData = [];
    
    videoArticles.forEach((r, idx) => {
      videos.push({ idx: idx });
      
      const speaker = r.Author ? r.Author.trim() : '';
      const source = r.RSS_Source || 'Presentation Source';
      const metaText = speaker ? `${speaker} · ${source}` : source;
      
      brandVideoData.push({
        company: (r.Competitor || 'Market').split(',')[0].trim(),
        title: r.Title,
        duration: Math.max(2, Math.round((r.News_Body || '').split(' ').length / 150)),
        badge: (r.Topic || 'CXO Keynote').toUpperCase(),
        meta: metaText,
        body: r.News_Body || 'No text extracted.',
        source: source,
        url: r.Article_URL || '#'
      });
    });
    
    if (videos.length === 0) {
      videos.push({ idx: 0 });
      brandVideoData.push({
        company: "TABHI ENGINE",
        title: "Competitor Market Summary Brief",
        duration: 3,
        badge: "INFO BRIEF",
        meta: "Summary of market shifts across monitored brands.",
        body: "No critical competitor threat actions detected. Sector trends remain within predicted boundaries.",
        source: "Tabhi Analytics",
        url: "#"
      });
    }
    
    this.brandVideoData[brandId] = brandVideoData;
    
    return {
      title: brandMeta.title,
      label: brandMeta.label,
      headerBadge: brandMeta.headerBadge,
      heroTitle: brandMeta.heroTitle,
      heroDesc: brandMeta.heroDesc,
      footerLeft: brandMeta.footerLeft,
      stats: stats,
      ticker: ticker,
      insights: insights,
      overviewCols: overviewCols,
      growthCols: growthCols,
      productCols: productCols,
      videos: videos
    };
  }
  
  mapRowToCard(r) {
    const topic = r.Topic || 'General';
    const sentiment = r.Sentiment || 'Neutral';
    const threat = r.Threat_Level || 'Low';
    
    // Format published date
    let timeStr = 'Recently';
    if (r.Published_Date) {
      try {
        const pubDate = new Date(r.Published_Date);
        const diffMs = new Date() - pubDate;
        const diffHrs = Math.floor(diffMs / (1000 * 60 * 60));
        if (diffHrs < 1) {
          timeStr = 'Just now';
        } else if (diffHrs < 24) {
          timeStr = `${diffHrs}h ago`;
        } else {
          timeStr = pubDate.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
        }
      } catch(e) {
        timeStr = r.Published_Date;
      }
    }
    
    return {
      id: r.Article_ID,
      company: (r.Competitor || 'Unknown').toUpperCase().split(',')[0].trim(),
      logo: (r.Competitor || '??').substring(0, 2).toUpperCase(),
      time: timeStr,
      title: r.Title,
      tags: [topic.toUpperCase(), sentiment.toUpperCase(), threat.toUpperCase() + ' THREAT'],
      source: r.RSS_Source || 'News Source',
      body: r.News_Body || '',
      url: r.Article_URL || '#',
      criticalityScore: Number(r.Criticality_Score) || 0,
      priorityTier: r.Priority_Tier || 'Tier 4 - Low'
    };
  }
  
  getBrandData(brandId) {
    return this.data[brandId];
  }
  
  getEmptyBrandDataset(brandId) {
    return {
      title: `${brandId.toUpperCase()} (B2X)`,
      label: `${brandId.toUpperCase()} RADAR LIVE`,
      headerBadge: "RADAR OFFLINE",
      heroTitle: "No Data Loaded",
      heroDesc: `Please run the News Intelligence scraper and copy the database sheets to your public/data folder or place them in News_Dashboard/data/raw_news_database_${brandId.charAt(0).toUpperCase() + brandId.slice(1)}.xlsx.`,
      footerLeft: "TABHI · Offline Mode",
      stats: { overview: [], 'growth-marketing': [], 'product-strategy': [] },
      ticker: [{ tag: "OFFLINE", text: "Database sheets not found in data/ folder.", isHighlight: true }],
      insights: { overview: ["Excel database sheet not found. Run 'python src/main.py' to generate databases first."], 'growth-marketing': [], 'product-strategy': [] },
      overviewCols: [], growthCols: [], productCols: [], videos: []
    };
  }
  
  isToday(dateStr) {
    if (!dateStr) return false;
    try {
      const d = new Date(dateStr);
      const today = new Date();
      return d.getDate() === today.getDate() && d.getMonth() === today.getMonth() && d.getFullYear() === today.getFullYear();
    } catch(e) {
      return false;
    }
  }
}
