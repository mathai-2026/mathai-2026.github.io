---
layout: page
title: MATH-AI
subtitle: "The 6th Workshop on Mathematical Reasoning and AI"
use-site-title: true
---
<div class="venue" style="font-size: 27px; display: block; font-family: 'Open Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif; font-weight: 300; color: #404040; text-align: center;">
  NeurIPS 2026, Atlanta, December 11–13, 2026 (exact date &amp; room TBD)
</div>




<div class="sharethis-inline-share-buttons"></div>
<meta name="thumbnail" content="./img/neurips-logo-new.jpg" />

# News
<!-- * The <a href="https://mathai-2026.github.io/cfp/">call for papers</a> is now open! -->



# Overview

Mathematical reasoning is central to science, engineering, finance, education, and mathematics itself. Since the first MATH-AI workshop, the field has moved from asking whether large language models (LLMs) can solve mathematical problems to asking how AI systems can participate across the gamut of mathematical research: proposing conjectures, searching for examples and counterexamples, formalizing arguments, proving theorems, designing algorithms, and collaborating with human researchers.

This year, our workshop focuses more squarely on (but is not limited to) the intersection of agentic AI and mathematical reasoning. Recent progress makes this an especially timely moment for the 6th MATH-AI workshop at NeurIPS: AI systems have achieved super-human results on competition-style and formal mathematical reasoning tasks, autoformalization is connecting natural mathematical language with proof assistants and formal libraries, and AI systems are beginning to guide mathematical discovery in topology, representation theory, combinatorics, matrix multiplication, and geometry. These advances point toward "auto-research," in which AI helps automate parts of the research loop from conjecture generation to proof search, verification, and communication.

This year, our central question is: *How can agentic AI systems advance mathematical research while remaining reliable collaborators for human mathematicians?* This theme links two priorities: building agents that can plan, use tools, conjecture, formalize, prove, verify, and learn from feedback; and designing human-AI workflows in which such agents extend mathematical judgment. It preserves the central question of previous MATH-AI workshops while reflecting the field's shift from isolated problem solving toward reliable mathematical agents and human-AI research workflows. To address this question, we aim to bring together diverse participants from different backgrounds, institutions, and disciplines into our workshop. Our objective is to foster a lively and constructive dialogue on areas related, but not limited, to the following:

- **Humans vs. machines**: How do human and machine mathematical reasoning differ, complement one another, or intersect?
- **Measuring mathematical reasoning**: How do we design benchmarks that capture proof quality, robustness, creativity, and formal correctness?
- **New capabilities**: How do we build AI agents that conjecture, explore, prove, formalize, and self-improve through reliable feedback?
- **Auto-research and discovery**: Which parts of mathematical research can be automated, and how should human-AI teams divide labor?
- **Education**: What roles can deep learning models play in mathematics education, especially where resources are limited?
- **Applications**: What applications could AI-assisted mathematics enable in formal verification, software and hardware design, science, engineering, finance, education, and mathematics itself?


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


# Sponsors

Sponsor information will be posted soon.


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
