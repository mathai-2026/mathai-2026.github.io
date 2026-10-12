---
layout: page
title: MATH-AI
subtitle: "The 6th Workshop on Mathematical Reasoning and AI"
use-site-title: true
---
<div class="venue" style="font-size: 27px; display: block; font-family: 'Open Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif; font-weight: 300; color: #404040; text-align: center;">
  NeurIPS 2026, Atlanta Hall C3, Saturday, December 12, 2026
</div>

# Accepted Papers

{% if site.data.accepted_papers and site.data.accepted_papers.size > 0 %}
<ol>
  {% assign accepted_papers = site.data.accepted_papers | sort: 'number' %}
  {% for paper in accepted_papers %}
  <li>{{ paper.title | escape }} <a href="{{ paper.url | escape }}">[paper]</a></li>
  {% endfor %}
</ol>

The list of accepted papers can also be found on [OpenReview](https://openreview.net/group?id=NeurIPS.cc/2026/Workshop/MATH-AI).
{% else %}
Accepted papers will be posted here after decisions are made.
{% endif %}

# Reviewers

{% if site.data.reviewer_acknowledgements and site.data.reviewer_acknowledgements.size > 0 %}
We thank the following reviewers for completing all their assigned reviews and helping make the workshop possible:

<ul>
  {% for reviewer in site.data.reviewer_acknowledgements %}
  <li>{{ reviewer.name | escape }}</li>
  {% endfor %}
</ul>
{% else %}
Reviewer acknowledgements will be posted here shortly before the workshop.
{% endif %}

