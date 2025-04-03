(function() {
    class AmazonScraper {
        constructor() {
            this.title = "";
            this.brand = "";
            this.asin = "";
            this.price = "";
            this.rating = "";
            this.review_count = "";
            this.imageUrls = [];
            this.description = "";
            this.bulletPoints = [];
            this.bestSellersRank = "";
            this.dateFirstAvailable = "";
        }

        async scrape() {
            try {
                // Scrape Best Sellers Rank
                const rankElement = document.querySelector('#productDetails_detailBullets_sections1 th:contains("Best Sellers Rank"), #detailBullets_feature_div span:contains("Best Sellers Rank")');
                if (rankElement) {
                    const rankParent = rankElement.closest('tr, li');
                    if (rankParent) {
                        this.bestSellersRank = rankParent.textContent.trim()
                            .replace(/Best Sellers Rank:|#/g, '')
                            .replace(/\s+/g, ' ')
                            .trim();
                    }
                }

                // Scrape Date First Available
                const dateElement = document.querySelector('#productDetails_detailBullets_sections1 th:contains("Date First Available"), #detailBullets_feature_div span:contains("Date First Available")');
                if (dateElement) {
                    const dateParent = dateElement.closest('tr, li');
                    if (dateParent) {
                        this.dateFirstAvailable = dateParent.textContent
                            .replace('Date First Available:', '')
                            .trim();
                    }
                }

                // Alternative selectors for different page layouts
                if (!this.bestSellersRank) {
                    const altRankElement = document.querySelector('#SalesRank, #productDetails_db_sections .prodDetSectionEntry:contains("Best Sellers Rank")');
                    if (altRankElement) {
                        this.bestSellersRank = altRankElement.textContent
                            .replace(/Amazon Best Sellers Rank:|#/g, '')
                            .replace(/\s+/g, ' ')
                            .trim();
                    }
                }

                if (!this.dateFirstAvailable) {
                    const altDateElement = document.querySelector('#productDetails_db_sections .prodDetSectionEntry:contains("Date First Available")');
                    if (altDateElement) {
                        this.dateFirstAvailable = altDateElement.textContent
                            .replace('Date First Available:', '')
                            .trim();
                    }
                }

                return {
                    title: this.title,
                    brand: this.brand,
                    asin: this.asin,
                    price: this.price,
                    rating: this.rating,
                    review_count: this.review_count,
                    imageUrls: this.imageUrls,
                    description: this.description,
                    bulletPoints: this.bulletPoints,
                    bestSellersRank: this.bestSellersRank,
                    dateFirstAvailable: this.dateFirstAvailable
                };
            } catch (error) {
                console.error('Scraping error:', error);
                throw error;
            }
        }
    }

    // Export the scraper
    window.AmazonScraper = AmazonScraper;
})(); 