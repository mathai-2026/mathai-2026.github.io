---
layout: page
title: MATH-AI
subtitle: "The 6th Workshop on Mathematical Reasoning and AI"
use-site-title: true
---
<div class="venue" style="font-size: 27px; display: block; font-family: 'Open Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif; font-weight: 300; color: #404040; text-align: center;">
  NeurIPS 2026, Atlanta, December 12 or 13, 2026 (exact date &amp; room TBA)
</div>




<div class="sharethis-inline-share-buttons"></div>
<meta name="thumbnail" content="./img/neurips-logo-new.jpg" />

# News

* We are delighted to announce that MATH-AI 2026 has been accepted as a NeurIPS 2026 workshop in Atlanta.


# Overview

Mathematical reasoning is central to science, engineering, finance, education, and mathematics itself. Since the first MATH-AI workshop, the field has moved from asking whether large language models (LLMs) can solve mathematical problems to asking how AI systems can participate across the gamut of mathematical research: proposing conjectures, searching for examples and counterexamples, formalizing arguments, proving theorems, designing algorithms, and collaborating with human researchers.

This year, our workshop focuses more squarely on (but is not limited to) the intersection of agentic AI and mathematical reasoning. Recent progress makes this an especially timely moment: AI systems have achieved super-human results on competition-style and formal mathematical reasoning tasks, autoformalization is connecting natural mathematical language with proof assistants and formal libraries, and AI systems are beginning to guide mathematical discovery in topology, representation theory, combinatorics, matrix multiplication, and geometry. These advances point toward automated mathematical discovery, in which AI helps automate parts of the research loop from conjecture generation to proof search, verification, and communication.

This year, our central question is: *How can agentic AI systems advance mathematical research while remaining reliable collaborators for human mathematicians?* This theme links two priorities: building agents that can plan, use tools, conjecture, formalize, prove, verify, and learn from feedback; and designing human-AI workflows in which such agents extend mathematical judgment. It preserves the central question of previous MATH-AI workshops while reflecting the field's shift from isolated problem solving toward reliable mathematical agents and human-AI research workflows. To address this question, we aim to bring together diverse participants from different backgrounds, institutions, and disciplines into our workshop. Our objective is to foster a lively and constructive dialogue on areas related, but not limited, to the following:

- **Humans vs. machines**: How do human mathematicians and agentic AI systems differ, complement one another, or collaborate as research partners?
- **Measuring mathematical reasoning**: How do we measure modern agentic systems on super-human mathematical tasks—using traditional metrics such as accuracy and formal correctness, and going beyond them to proof quality, interaction with proof environments, robustness, and creativity?
- **New capabilities**: How do we build AI agents that plan, use tools, conjecture, explore, prove, formalize, verify, and self-improve through reliable feedback?
- **Automated mathematical discovery**: Which parts of the mathematical research loop can agents automate, and how should human-AI teams divide labor, especially in long-horizon or open-ended research settings?
- **Education**: What roles can agentic AI systems play in mathematics education—tutoring, guiding exploration, and providing feedback—especially where resources are limited?
- **Applications**: What critical applications could mathematical agents enable in formal verification, software and hardware design, science, engineering, finance, and mathematics itself?


<hr>

# Speakers & Panelists
<div class="container" style="margin-top: 20px;margin-bottom: 0px;">
  <div class="row">
    {% for p in site.data.speakers %}
    {% if forloop.index<=5 %}
    {% capture id %}{{ p[0] }}{% endcapture %}
    {% include profile.html p=p %}
    {% endif %}
    {% endfor %}
  </div>
  <div class="row">
    {% for p in site.data.speakers %}
    {% capture id %}{{ p[0] }}{% endcapture %}
    {% if forloop.index>5 and forloop.index<=10%}
    {% include profile.html p=p %}
    {% endif %}
    {% endfor %}
  </div>
</div>

<hr>

# Organizers
<!-- # Organizers -->

<!-- prettier-ignore -->
<div class="container" style="margin-top: 25px;margin-bottom: 40px;">
  <!-- <br> 
  <div class="row" style="margin: -30px;"> -->
  <div class="row">
    {% for p in site.data.organizers %}
    {% if forloop.index<=4 %}
    {% capture id %}{{ p[0] }}{% endcapture %}
    {% include profile.html p=p %}
    {% endif %}
    {% endfor %}
  </div>
  <div class="row">
    {% for p in site.data.organizers %}
    {% capture id %}{{ p[0] }}{% endcapture %}
    {% if forloop.index>4 and forloop.index<=8%}
    {% include profile.html p=p %}
    {% endif %}
    {% endfor %}
  </div>
</div>
<hr>

<!-- # Sponsors

Sponsor information will be posted soon. -->


# Past MATH-AI Workshops

<div class="container" style="margin-bottom: 10px;"></div>
- 5th MATH-AI Workshop at NeurIPS'25: [The 5th Workshop on Mathematical Reasoning and AI](https://mathai2025.github.io/)
- 4th MATH-AI Workshop at NeurIPS'24: [The 4th Workshop on Mathematical Reasoning and AI](https://mathai2024.github.io/)
- 3rd MATH-AI Workshop at NeurIPS'23: [The 3rd Workshop on Mathematical Reasoning and AI](https://mathai2023.github.io/)
- 2nd MATH-AI Workshop at NeurIPS'22: [Toward Human-Level Mathematical Reasoning](https://mathai2022.github.io/)
- 1st MATH-AI Workshop at ICLR'21: [The Role of Mathematical Reasoning in General Artificial Intelligence](https://mathai-iclr.github.io/)
- MATHAI4ED Workshop at NeurIPS'21: [Math AI for Education: Bridging the Gap Between Research and Smart Education](https://mathai4ed.github.io/)

<div class="container" style="margin-bottom: 10px;"></div>


<hr>

Contact: <psong2@andrew.cmu.edu>.
