# Booking Benchmark

## Overview

This project focuses on the `booking_benchmark`, a benchmark for evaluating agentic capabilities of different instruction based VLMs on GUI task. the provided dataset has been created for the single-step-action of booking a flight task. The project includes a custom dataset, scripts for data processing, and an agent for real-time GUI interaction.

## Dataset

The dataset used in this benchmark was created specifically for this project. An annotated version of the dataset is available, which was generated with the help of the Omniparser tool.

## Tools and Environment

The data processing and model training were performed in a Google Colab environment. The following tools and scripts are included in this repository:

*   **Omniparser Script:** The script used to annotate the dataset.
*   **Notebooks:** 

## Real-time Application

To showcase the real-time application of the agent, the `WebAgent` was developed. This agent utilizes a Vision Language Model (VLM)(Gemini with Omniparser for parsing the contents of web environment) to interact with a graphical user interface (GUI), demonstrating the practical application of the benchmark.
