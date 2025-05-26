
def create_sample_data(data):
    # Create or get link
    link, created = Link.objects.get_or_create(
        url=data.get('url'),
        defaults={
            'title': data.get('title', ''),
            'description': data.get('meta_description', '')
        }
    )

    # Create or update SERP content
    serp_content, created = SerpContent.objects.update_or_create(
        link=link,
        defaults={
            'url': data.get('url'),
            'read_more_link': data.get('read_more_link', ''),
            'language': data.get('language', 'en'),
            'title': data.get('title', ''),
            'text': data.get('text', ''),
            'summary': data.get('summary', ''),
            'top_image': data.get('top_image', ''),
            'meta_img': data.get('meta_img', ''),
            'images': data.get('images', []),
            'movies': data.get('movies', []),
            'keywords': data.get('keywords', []),
            'tags': data.get('tags'),
            'authors': data.get('authors', []),
            'meta_keywords': data.get('meta_keywords', []),
            'meta_description': data.get('meta_description', ''),
            'meta_lang': data.get('meta_lang', ''),
            'meta_favicon': data.get('meta_favicon', ''),
            'meta_site_name': data.get('meta_site_name', ''),
            'canonical_link': data.get('canonical_link', ''),
            'publish_date': data.get('publish_date'),
        }
    )

if __name__ == "__main__":
    data= {
        "url": "https://www.nobelprize.org/prizes/peace/1901/dunant/facts/",
        "read_more_link": "",
        "language": "en",
        "title": "Henry Dunant – Facts",
        "top_image": "https://www.nobelprize.org/images/dunant-13538-landscape-medium.jpg",
        "meta_img": "https://www.nobelprize.org/images/dunant-13538-landscape-medium.jpg",
        "images": [
            "https://www.nobelprize.org/images/dunant-13538-portrait-medium.jpg",
            "https://www.nobelprize.org/images/educational-games-prisoners-of-war123752-landscape-x-large.jpg",
            "https://www.nobelprize.org/uploads/2023/10/nobelprizes_2023-1024x676.jpg",
            "https://www.nobelprize.org/wp-content/themes/nobelprize/assets/images/spinner.gif"
        ],
        "movies": [],
        "keywords": [],
        "meta_keywords": [
            ""
        ],
        "tags": None,
        "authors": [],
        "publish_date": None,
        "summary": "",
        "meta_description": "The Nobel Peace Prize 1901 was divided equally between Jean Henry Dunant \"for his humanitarian efforts to help wounded soldiers and create international understanding\" and Frédéric Passy \"for his lifelong work for international peace conferences, diplomacy and arbitration\"",
        "meta_lang": "en",
        "meta_favicon": "https://www.nobelprize.org/uploads/2018/08/Nobel-favicon-50x50.png",
        "meta_site_name": "NobelPrize.org",
        "canonical_link": "https://www.nobelprize.org/prizes/peace/1901/dunant/facts/",
        "text": "Founder of the Red Cross\n\nIn 1859, a battle was raging at the town of Solferino in Northern Italy. There the Swiss businessman Henry Dunant saw thousands of Italian, French and Austrian soldiers killing and maiming each other. On his own initiative, he organized aid work. Later he wrote the book A Memory of Solferino, which contained a plan: all countries should form associations to help the sick and wounded on the battlefield - whichever side they belonged to.\n\nThe result was the establishment of the International Committee of the Red Cross in 1863, and the adoption of the Geneva Convention in the following year. It laid down that all wounded soldiers in a land war should be treated as friends. Medical personnel would be protected by the red cross in a white field.\n\nFor Dunant personally, financial difficulties led to poverty and loss of social respect. But the organization he had created grew, and the underlying ideas won gradual acceptance. It pleased the ageing Dunant that the Norwegian Nobel Committee rewarded his life's work with the Nobel Peace Prize."
    }

    create_sample_data(data)