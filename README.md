# cs144-proposal

eric mazumdarr is so annoying and stupid and I hate him - anonymous

Seller node fields (per store/vendor)
- name
- location (lat/long or neighborhood)
- tags (style keywords: “y2k”, “vintage denim”, “minimalist”, “streetwear”, “goth”, etc.)
- price_level (cheap/med/high or 1–3)
- “hidden_gem_score” proxy (optional; could be derived from your own ratings)

User node fields
- name (or anonymized ID)
- style preferences tags (optional)

Edges
- user–seller: {type: visited / liked / “hidden gem find”, rating 1–5, tags like “great jeans”, “unique jewelry”}
- user–user: friend link (simple)
- seller–seller: weighted similarity (computed)

--

users.csv
- price_sensitivity, trend_affinity, exploration_level are 0–1 floats.
- style_tags are semicolon-separated so they’re easy to split.

friendships.csv: Undirected social links

user_style_profiles.csv
- Weights over styles so you can score recommendations later even before you have sellers.

