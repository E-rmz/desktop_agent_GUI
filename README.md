# Booking Benchmark

## Overview

This project introduces **Booking Benchmark**, a framework for evaluating the agentic capabilities of instruction-based vision–language models (VLMs) on GUI tasks. It provides:

- A **single‑step flight‑booking** dataset  
- Data‑processing and annotation scripts  
- An interactive agent for real‑time GUI automation  

## Dataset

The benchmark dataset was created from scratch. An **annotated** version—generated with the Omniparser tool—is also included.

## Tools and Environment

All data processing and model training were performed in **Google Colab**. This repository contains:

- **Omniparser Script**  
  - Annotates the raw dataset  
  - Defines `requirements.txt` for installing dependencies  
  - Loads model weights directly  

- **Omniparser_API.py**  
  - Integrated into the WebAgent  
  - Calls the Omniparser service via its Hugging Face Space API  

- **utils‑dataset‑testing/**  
  - Utilities for dataset creation and validation  

- **screenshots/**  
  - Raw and annotated GUI screenshots  
  - Subfolders with outputs for each model evaluation  

## Evaluation (Part 1)

Model evaluation is documented in `booking_benchmark.ipynb`. To reproduce the results:

1. Run all cells **in order**.  
2. Flush the GPU before switching to a different model.  
3. Provide your **Hugging Face** token and **Gemini API** key when prompted.

## Real‑World Application (Part 2)

`WebAgent.ipynb` demonstrates a production‑style agent built with the **Langgraph** framework. The agent uses:

- A VLM (Gemini)  
- Omniparser for parsing web‑page contents  
- Deined Tools

To reproduce the demo:

1. Run all cells **up to** the **Examples** section.  
2. For each example, initialize browser state(the cell before calling `call_agent` ).  
3. Invoke `call_agent(prompt)` with your desired instruction.  
