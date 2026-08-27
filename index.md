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

* **Timeline update:** Due to NeurIPS paper-import policies and related conference updates this year, we are adjusting our schedule and cannot extend submissions as late into September as in prior years (when we aimed to accommodate concurrent ICLR submissions). **Paper submissions are now due September 6, 2026 (AoE)**; reviews are due September 20; author notification by September 29 (all AoE). We still welcome **4-page** submissions—please submit preliminary drafts if needed. Full details are on the [call for papers](/cfp).
* Join our [Discord](https://discord.gg/A8GfNhhCT) server to stay up to date with MATH-AI announcements, news, and discussions, and connect with fellow members of the community.
* The [call for papers](/cfp) is now open! Submit on [OpenReview](https://openreview.net/group?id=NeurIPS.cc/2026/Workshop/MATH-AI).
* We are calling for reviewers! Please nominate yourself or others via our [reviewer nomination form](https://docs.google.com/forms/d/e/1FAIpQLSenuh8uLvudlAA0ifF-pGU_XjpgU7CINQBFeDC0Acq_tIq2YQ/viewform?usp=header).
* We are delighted to announce that MATH-AI 2026 has been accepted as a NeurIPS 2026 workshop in Atlanta.

# Key Dates

**Paper submission opens:** July 25, 2026 <br>
**Paper submission deadline:** September 6, 2026 (AoE) <br>
**Reviewing deadline:** September 20, 2026 (AoE) <br>
**Author notification:** September 29, 2026 (AoE) <br>
**Camera-ready deadline:** October 3, 2026 (AoE) <br>
**Workshop:** December 12 or 13, 2026 (TBA)

See the [call for papers](/cfp) for full submission details.


# Overview

Mathematical reasoning is central to science, engineering, finance, education, and mathematics itself. Since the first MATH-AI workshop, the field has moved from asking whether large language models (LLMs) can solve mathematical problems to asking how AI systems can participate across the full range of mathematical research: proposing conjectures, searching for examples and counterexamples, formalizing arguments, proving theorems, designing algorithms, and collaborating with human researchers.

This year, our workshop focuses more squarely on (but is not limited to) the intersection of agentic AI and mathematical reasoning. Recent progress makes this an especially timely moment: AI systems have achieved super-human results on competition-style and formal mathematical reasoning tasks, autoformalization is connecting natural mathematical language with proof assistants and formal libraries, and AI systems are beginning to guide mathematical discovery in topology, representation theory, combinatorics, matrix multiplication, and geometry. These advances point toward automated mathematical discovery, in which AI helps automate parts of the research loop from conjecture generation to proof search, verification, and communication.

This year, our central question is: *How can agentic AI systems advance mathematical research while remaining reliable collaborators for human mathematicians?* This theme links two priorities: building agents that can plan, use tools, conjecture, formalize, prove, verify, and learn from feedback; and designing human-AI workflows in which such agents extend mathematical judgment. It preserves the central question of previous MATH-AI workshops while reflecting the field's shift from isolated problem solving toward reliable mathematical agents and human-AI research workflows. To address this question, we aim to bring together diverse participants from different backgrounds, institutions, and disciplines into our workshop. Our objective is to foster a lively and constructive dialogue on areas related, but not limited, to the following:

- **Humans vs. machines**: What are the comparative strengths, limitations, and characteristic failure modes of human mathematicians and AI systems? Which aspects of mathematical reasoning, judgment, and creativity remain distinctively human or machine?
- **Building reliable mathematical agents**: What architectures, training methods, memory systems, tool interfaces, and feedback mechanisms enable agents to plan over long horizons, recover from errors, and operate reliably in mathematical environments?
- **Evaluating mathematical agents**: How should we evaluate agents on advanced and open-ended mathematical tasks—beyond answer accuracy and formal correctness—to capture proof quality, robustness, creativity, efficiency, and effective use of tools and feedback?
- **Automated mathematical research**: Which parts of the mathematical research process can agents conduct autonomously—from problem selection and experimentation to conjecture refinement and verification—and how should human researchers supervise, redirect, and collaborate with them?
- **Education**: What roles can agentic AI systems play in mathematics education—tutoring, guiding exploration, and providing feedback—especially where expert instruction and educational resources are limited?
- **Cross-domain applications**: How can mathematical agents enable progress in formal verification, software and hardware design, science, engineering, finance, and other domains that depend on complex mathematical reasoning?


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

Contact: <mathai.neurips2026@gmail.com>.
