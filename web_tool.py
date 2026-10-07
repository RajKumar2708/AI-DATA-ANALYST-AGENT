from tavily import TavilyClient
import os
from dotenv import load_dotenv

load_dotenv()

tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

def web_search(query):
    response = tavily_client.search(
        query,
        max_results=3
    )

    results = []

    for result in response["results"]:
        results.append({
            "title": result["title"],
            "url": result["url"],
            "content": result["content"][:1500]
        })

    return str(results)

# {
#   "query": "Compare the performance of Tesla and Ford in the EV market",
#   "answer": null,
#   "images": [],
#   "results": [
#     {
#       "url": "https://www.facebook.com/fb-answers/tesla-vs-ford-ev-market-performance-comparison",
#       "title": "Tesla Vs Ford Ev Market Performance Comparison",
#       "content": "Tesla still leads EV production with about 1.64 million units in 2025 versus Ford's roughly 105,000, but Ford is gaining ground in the U.S. non-luxury segment",
#       "score": 0.9302622,
#       "raw_content": null,
#       "id": "06fd32-00"
#     },
#     {
#       "url": "https://www.downelink.com/tesla-vs-ford-a-complete-electric-vehicle-comparison",
#       "title": "Tesla vs Ford: A Complete Electric Vehicle Comparison - DowneLink",
#       "content": "Meanwhile, Ford suffered declining sales since 2018 primarily due to issues like production constraints. The rapid growth in EV segment share shows tremendous promise. According to Experian automotive data, the Ford Mustang Mach-E captured 9.4% share of the total EV market in Q1 2023 while the Lightning captured 4.2% of EV sales since launch (3). Consumer reception of new EV launches points towards a brighter future.\n\nComparing revenue and profitability also showcases…\n\n[Additional 1,000+ words expanding the financials and growth analysis along with other major sections highlighted previously]\n\nI hope this complete guide has presented an unbiased, data-driven comparison of Tesla and Ford electric vehicles. Please reach out with any other questions!\n\n1. \n2. \n3. \n\n### You May Like to Read, [...] With Tesla devoted exclusively to electric drivetrains and Ford balancing internal combustion and electric lineups, this table showcases the current model similarities and differences. While Tesla offers more range on paper, recent reviews have found Ford‘s range numbers align closely with real-world driving.\n\nFord‘s electric models leverage nostalgic nameplates in the Mustang, Lightning and E-Transit which may appeal to longtime fans of those vehicles. However, Tesla‘s lineup feels more futuristic with the high-tech interiors and eccentric Cybertruck design.\n\n## EV Sales and Revenue Growth Trends\n\nReviewing historical delivery and sales data showcases the meteoric rise of Tesla from startup to leading US automaker while Ford‘s steady sales lag, especially recently with part shortages. [...] | Year | Tesla Deliveries | Tesla Year/Year Growth | Ford US Sales | Ford Year/Year Growth |\n ---  --- \n| 2018 | 245,240 | +145% | 2,497,318 | -3.5% |\n| 2019 | 367,656 | +50% | 2,422,698 | -3% |\n| 2020 | 499,535 | +36% | 2,047,069 | -15.5% |\n| 2021 | 936,172 | + 87% | 1,896,562 | -7.4% |\n\n\"Tesla‘s vehicle delivery growth since 2018 is simply unprecedented expansion in automotive history\" remarks Sandy Munro, longtime industry analyst and CEO of Munro & Associates. He adds \"assuming continued 50%+ annual increases, Tesla could reasonably top 2 million deliveries in 2023 which would rival Toyota and GM as the world‘s top auto manufacturer\" (2).",
#       "score": 0.88822687,
#       "raw_content": null,
#       "id": "a3859a-01"
#     },
#     {
#       "url": "https://stockdividendscreener.com/auto-manufacturers/ford-vs-tesla-stock-in-margin-and-profitability",
#       "title": "Ford vs Tesla: Revenue, Sales, and Vehicle Profit Margin | Fundamental Data And Statistics For Stocks",
#       "content": "Structural Takeaway: The Ford vs. Tesla comparison in 2025 does not have a clear winner — it has two companies experiencing simultaneous distress from different directions. Ford’s FY2025 collapse (-$0.5B gross profit, -$9.2B operating profit) is the more acute near-term crisis. Tesla’s volume stagnation and margin compression represent a more strategic long-run concern. The 3-year averages capture a transition period for both: Ford moving from legacy profitability toward EV-related losses, and Tesla moving from peak margin toward a more competitive, lower-priced equilibrium. The next two years will be decisive for both companies and the comparison will look materially different depending on whether Ford’s EV losses stabilise and whether Tesla’s next model cycle (refreshed Model Y, new [...] Vehicle volumes tell opposite stories: Ford is stable, Tesla is contracting. Ford wholesale volumes have been remarkably consistent at 4.2–4.5 million units across 2022–2025, with the 3-year average of 4,426,000 units reflecting a steady if unspectacular commercial vehicle and truck franchise. Tesla peaked at 1,808,581 deliveries in 2023, declined to 1,789,226 in 2024 (-1.1%), and contracted sharply to 1,636,129 in 2025 (-8.6%) — the 3-year average of 1,744,645 units represents a business that has stalled in volume terms after a decade of hypergrowth. Whether this is temporary (brand perception, political headwinds in the U.S. and Europe, awaiting new model cycle) or structural (market saturation, intensifying Chinese competition) is the most contested question in Tesla’s investment [...] Tesla has undergone its own margin compression, but from a position of structural strength. Tesla’s automotive gross margin peaked at 26.5% in 2021 and 26.2% in 2022 — a level no mass-market automaker has achieved in modern history — before compressing to 17.1% (2023), 14.6% (2024), and 14.5% (2025). The 3-year average of 15.4% is lower than Tesla bulls would have forecast three years ago, but remains far ahead of Ford’s 5.8% average. Tesla’s operating margin followed a similar arc: from 16.8% in 2022 to 4.6% in 2025, with a 3-year average of 7.0%. The compression reflects deliberate price reductions to defend volume share against Chinese EV competition, increased R&D spend, and the cost of production ramp (Cybertruck, new Gigafactories). Unlike Ford, Tesla’s margin compression is",
#       "score": 0.8834878,
#       "raw_content": null,
#       "id": "f55a4f-02"
#     },
#     {
#       "url": "https://stockdividendscreener.com/auto-manufacturers/ford-vs-tesla-stock-in-margin-and-profitability#respond",
#       "title": "Ford vs Tesla: Revenue, Sales, and Vehicle Profit Margin | Fundamental Data And Statistics For Stocks",
#       "content": "Structural Takeaway: The Ford vs. Tesla comparison in 2025 does not have a clear winner — it has two companies experiencing simultaneous distress from different directions. Ford’s FY2025 collapse (-$0.5B gross profit, -$9.2B operating profit) is the more acute near-term crisis. Tesla’s volume stagnation and margin compression represent a more strategic long-run concern. The 3-year averages capture a transition period for both: Ford moving from legacy profitability toward EV-related losses, and Tesla moving from peak margin toward a more competitive, lower-priced equilibrium. The next two years will be decisive for both companies and the comparison will look materially different depending on whether Ford’s EV losses stabilise and whether Tesla’s next model cycle (refreshed Model Y, new [...] Vehicle volumes tell opposite stories: Ford is stable, Tesla is contracting. Ford wholesale volumes have been remarkably consistent at 4.2–4.5 million units across 2022–2025, with the 3-year average of 4,426,000 units reflecting a steady if unspectacular commercial vehicle and truck franchise. Tesla peaked at 1,808,581 deliveries in 2023, declined to 1,789,226 in 2024 (-1.1%), and contracted sharply to 1,636,129 in 2025 (-8.6%) — the 3-year average of 1,744,645 units represents a business that has stalled in volume terms after a decade of hypergrowth. Whether this is temporary (brand perception, political headwinds in the U.S. and Europe, awaiting new model cycle) or structural (market saturation, intensifying Chinese competition) is the most contested question in Tesla’s investment [...] Tesla has undergone its own margin compression, but from a position of structural strength. Tesla’s automotive gross margin peaked at 26.5% in 2021 and 26.2% in 2022 — a level no mass-market automaker has achieved in modern history — before compressing to 17.1% (2023), 14.6% (2024), and 14.5% (2025). The 3-year average of 15.4% is lower than Tesla bulls would have forecast three years ago, but remains far ahead of Ford’s 5.8% average. Tesla’s operating margin followed a similar arc: from 16.8% in 2022 to 4.6% in 2025, with a 3-year average of 7.0%. The compression reflects deliberate price reductions to defend volume share against Chinese EV competition, increased R&D spend, and the cost of production ramp (Cybertruck, new Gigafactories). Unlike Ford, Tesla’s margin compression is",
#       "score": 0.8834878,
#       "raw_content": null,
#       "id": "be59c0-03"
#     },
#     {
#       "url": "https://www.researchgate.net/publication/387065231_Comparative_Analysis_of_Tesla_and_Ford_Investment_Recommendations_Based_on_the_7Ps_Marketing_Portfolio_and_Porter's_Five_Forces_Model",
#       "title": "(PDF) Comparative Analysis of Tesla and Ford: Investment ...",
#       "content": "Tesla's advantage lies in its forward-looking technology and market leadership, while Ford's lies in its stable financial performance and market",
#       "score": 0.87139857,
#       "raw_content": null,
#       "id": "ce1d0c-04"
#     },
#     {
#       "url": "https://intellectia.ai/news/stock/ford-and-tesla-revenue-analysis",
#       "title": "Ford and Tesla Revenue Analysis | Intellectia.AI",
#       "content": "Title: Ford and Tesla Revenue Analysis | Intellectia.AI\nFord and Tesla Revenue Analysis | Intellectia.AI. # Ford and Tesla Revenue Analysis. * **Ford's Steady Revenue**: Ford reported $43.3 billion in revenue for Q1 2026 with a 6% net income margin, indicating solid performance in the traditional automotive market despite challenges in its EV segment. * **Tesla's Revenue Fluctuations**: Tesla's Q1 2026 revenue reached $22.4 billion, reflecting a 16% year-over-year growth, showcasing rapid expansion in the EV market, although its free cash flow has significantly declined due to AI development costs. * **EV Market Competition**: Ford's EV sales were only $1.2 billion in Q1, indicating that its efforts in the electric vehicle sector have not resonated with consumers, highlighting competitive pressures from Tesla. * **New Business Development**: Ford's newly launched Energy division aims to diversify income by offering battery storage solutions, while Tesla focuses on developing its self-driving vehicle business, which could yield higher profit potential in the future. However, it is \"likely more benign than feared\" as Duffy's letter does not inherently stop Ford from using CATL's technology or alter the company's eligibility for tax credits, adds the analyst, who has an Equal Weight rating and $14 price target on Ford shares. Morgan Stanley lowered the firm's price target on Ford to $14 from $15 and keeps an Equal Weight rating on the shares. ## About F. The Ford Blue segment primarily includes the sale of Ford and Lincoln internal combustion engine (ICE) and hybrid vehicles, service parts, accessories, and digital services for retail customers. The Ford Model e segment primarily includes the sale of its electric vehicles, service parts, accessories, and digital services for retail customers. The Ford Pro segment primarily includes the sale of Ford and Lincoln vehicles, service parts, accessories, and services for commercial, government, and rental customers. The Ford Credit segment consists of the Ford Credit business on a consolidated basis, which is primarily vehicle-related financing and leasing activities. * **Ford's Strategic Shift**: Ford focuses on modernizing its business through the Ford+ plan, achieving nearly $187.3 billion in revenue for FY 2025, with a modest growth of 1.2%, yet facing a significant net loss of $8.2 billion, highlighting the challenges and opportunities during its transformation.",
#       "score": 0.86441374,
#       "raw_content": null,
#       "id": "56f371-05"
#     },
#     {
#       "url": "https://www.cellaford.com/ford-vs.-tesla-what-makes-the-best-electric.html",
#       "title": "Ford vs. Tesla: What Makes the Best Electric",
#       "content": "Driving Experience: Both offer instant torque and smooth acceleration characteristic of EVs. Ford often aims for a balance of comfort and sportiness, while Tesla can lean more towards sporty, performance-oriented driving.\n Design and Interior: Tesla's design is futuristic and minimalist. Ford's electric models, like the Mustang Mach-E and F-150 Lightning, incorporate familiar design elements from their traditional counterparts, offering a more conventional yet modern interior.\n Service and Support: Ford benefits from its vast, established dealership network, offering widespread service and maintenance. Tesla's service model is more centralized, with mobile service options available. [...] Range and Charging: Both brands offer impressive ranges, often exceeding 300 miles on a single charge for many models. Tesla has its proprietary Supercharger network, which is extensive, while Ford vehicles typically leverage the growing network of public charging stations and offer home charging solutions. When considering a new vehicle, it's always wise to check out our new Ford inventory to see specific range figures.\n Technology and Infotainment: Tesla is renowned for its minimalist interior and large touchscreen interface that controls nearly all vehicle functions. Ford, while integrating advanced tech, often retains more traditional physical controls alongside its touchscreens, which some drivers prefer. [...] Tesla's strengths lie in its sophisticated software, over-the-air updates that continually improve the vehicle, and its Supercharger network, which offers a convenient way to charge on the go. For drivers who prioritize the latest in automotive technology, minimalist aesthetics, and a strong emphasis on pure EV performance, Tesla presents a compelling option.\n\n## Comparing Key Factors: What Matters Most to You?\n\nWhen deciding between Ford and Tesla, consider these important aspects:",
#       "score": 0.8588255,
#       "raw_content": null,
#       "id": "f5f4af-06"
#     },
#     {
#       "url": "https://www.bakerinstitute.org/research/ford-vs-tesla-what-does-transformational-automobile-scale-look",
#       "title": "Ford vs. Tesla: What Does a Transformational Automobile Scale-Up Look Like? | Baker Institute",
#       "content": "The comparison between the first years of Tesla and Ford’s Model T sales is instructive due to at least two shared traits. First, each company rose to prominence on the back of a single revolutionary vehicle type. If the Model T had failed to catch on with consumers, Ford would have been out of business. Likewise, Tesla grew primarily due to Model S, X, and 3 sales, which brought high performance and a “cool” factor to the pure-battery EV market. [...] Second, each company was (or is) a market maker at the time it introduced the new vehicle type. The Model T dominated auto sales volumes in the 1910s and 1920s, while Tesla is the world's largest seller of battery-only, full-size EVs, accounting for nearly 80% sold in the US market during 2019.1 There is, however, an important distinction between the Ford and Tesla examples: the Model T dominated sales of all autos, while Tesla only dominates the battery EV space. In fact, Tesla accounts for less than 1% of new car sales in the US, and only about 0.48% of the sales volume in the overall global light duty vehicle (i.e., passenger cars, pickups, and SUVs) market.\n\nFigure 1 — Sales Trajectories of the Ford Model T and the Tesla Vehicle Suite [...] Tesla and other EV-focused manufacturers also face a different market environment than Ford did in the early 20th century. Incumbent automakers now operate valuable franchises that took decades and billions of dollars to build, and whose economic gravitational force the parent company will likely be unable to escape.\n\nUsing trucks as an example, Ford sold more than 900,000 F-Series trucks in 2018 alone, which is more cars than Tesla has sold cumulatively to date.3 Perhaps even more salient, Ford’s F-Series business alone likely generated close to $45 billion in revenue during 2018—a figure approximating Goldman Sach’s revenue that year and one that would have placed the F-Series business 65th on that year’s Fortune 500 list.4",
#       "score": 0.8458536,
#       "raw_content": null,
#       "id": "c99999-07"
#     },
#     {
#       "url": "https://www.youtube.com/watch?v=gM7Fl1MMdDw",
#       "title": "Tesla vs Ford EVs: Ford's FIGHT for Survival (Next Gen EVs)",
#       "content": "[3:28] many vehicles and in q34 delivered 14 as many vehicles as Tesla when it comes to the global scale in the full year of\n[3:36] 2022 Tesla delivered over 1.3 million Vehicles when it comes to Ford we know they delivered over 61 000 EVS in the\n[3:44] United States in 2022 and when it comes to battery electric vehicle deliveries in China and Europe we don't have exact numbers for those markets but we do have\n[3:52] some good sources which get us pretty close so based on my research and based on what I could find I estimate that\n[3:59] Ford globally delivered between 90 and 91 000 battery electric vehicles in 2022. so as you can see right now Tesla\n[4:08] is far ahead of Ford but gem had some things to say about Ford's EVP future goals and I'd like to dive into those [...] [2:47] when it comes to manufacturing capacity that's a big jump and being able to reduce uh somewhere close to 600 000\n[2:55] units per year would be a big jump for Ford now I do want to step back and just look at what Tesla is doing and compare\n[3:02] that to what Ford has done so far and then we'll talk about more uh further in the future goals from Ford from Jim Farley so if you look at the USA Market\n[3:11] only for instance and you look at how many battery electric vehicles that Tesla has sold in this market versus Ford you can see there that in Q4 of\n[3:20] 2022 Ford only delivered six percent as many vehicles as Tesla in the United States in q24 delivered 12 percent as [...] [15:47] percentage of a positive 6.6 percent when you compare this to Tesla in the full year of 2022 according to their Q4\n[15:54] 2022 investors update letter they were able to post a profit of 16.8 percent as a business in addition all of Ford's\n[16:03] profit right now comes from their internal combustion engine vehicle business because as was recently confirmed by a Ford representative and\n[16:10] was reported in this drive Tesla Canada article Ford's Chief customer officer the chief customer officer of Ford Model\n[16:17] E mentioned quote we are not profitable at this moment we've committed to being profitable in 26. we're currently on the",
#       "score": 0.8342047,
#       "raw_content": null,
#       "id": "ba00de-08"
#     },
#     {
#       "url": "https://explore.nemo.money/en/stocks/compare/tesla-vs-ford",
#       "title": "Tesla vs Ford: Which is the Better Buy in September 2026?",
#       "content": "Tesla dominates battery electric vehicle production while pushing into energy storage and autonomous driving, whereas Ford Motor has been manufacturing internal combustion vehicles for over a century and is now investing heavily to transition its lineup toward electrification. Both companies are betting enormous capital on the outcome of the EV transition, but from opposite starting positions. Tesla vs Ford dissects delivery volumes, software revenue potential, legacy pension obligations, EV gross margins, and which automaker's strategy better positions it for a future where the powertrain and the software stack define the winner. [...] Ford\n\n### Ford\n\n#### Pros\n\n Ford offers a high dividend yield of 6.63%, providing steady income for investors.\n Ford displays lower volatility at 8.65%, offering more stable price movements than Tesla.\n Ford plans eyes-off, hands-free driving technology by 2028, advancing competitiveness against Tesla.\n\n#### Considerations\n\n Ford lags in long-term performance with 3.08% annualised return over 10 years versus Tesla's 33.93%.\n Ford faces execution risks in transitioning to advanced autonomous driving amid industry competition.\n Ford remains exposed to cyclical automotive sector pressures and traditional engine dependencies.\n\n### Tesla (TSLA) Next Earnings Date [...] Ford Motor Company (ticker: F) is a legacy US automaker known for its F‑Series trucks, commercial vehicles and a growing electric‑vehicle (EV) lineup including the Mustang Mach‑E and F‑150 Lightning. The company combines large scale manufacturing, global distribution and brand recognition with a multi‑year push into electrification, software and services. Key considerations for investors include exposure to cyclical new‑vehicle demand, commodity and supply‑chain costs, and competition in the EV market. Profitability can be driven by strong truck and SUV sales, cost discipline and successful monetisation of software and connected services, but results may vary across cycles. With a market capitalisation near $49.99bn, Ford sits between legacy OEMs and EV challengers. This summary is for",
#       "score": 0.8338803,
#       "raw_content": null,
#       "id": "860354-09"
#     }
#   ],
#   "response_time": 4.91,
#   "request_id": "d79b6764-7ec0-4908-9baa-fe0fef3a062d"
# }





