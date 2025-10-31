# privacy-lab

**Privacy Lab** is an application and utility created to help firms explore how [privacy-enhancing technologies (PETs)](https://iabtechlab.com/pets) can be incorporated into digital advertising workflows and how doing so may impact their advertising operations.

## Quick Start - Web API Interface

Privacy Lab now includes a REST API and web interface for easy access to the PET workflows:

### Start the API Server
```bash
./start_api.sh
```
The API will be available at http://localhost:8000 with interactive docs at http://localhost:8000/docs

### Start the Web Interface
```bash
./start_web.sh
```
Then open http://localhost:8080 in your browser

### API Usage Example
```bash
# Differential Privacy
curl -X POST http://localhost:8000/api/differential-privacy \
  -H "Content-Type: application/json" \
  -d '{"epsilon": 1.0, "use_sample_data": true}'
```

See [README_API.md](README_API.md) for complete API documentation.

## Measurement and Attribution Workflow Variants Incorporating PETs

The `notebook` directory contains a Jupyter notebook with interactive examples that illustrate how selected PETs can be used to protect users' PII within a common digital advertising use case: measurement and attribution for digital advertising campaigns. The example workflows are informed by the IAB Tech Lab [Attribution Data Matching Protocol (ADMaP) specification](https://iabtechlab.com/admap/) and incorporate Universal CAPI v1. The included workflow variants are enumerated below.

* Privacy-preserving aggregation of conversion data using [*k*-anonymity](https://en.wikipedia.org/wiki/K-anonymity)
* Privacy-preserving aggregation of conversion data using [differential privacy (DP)](https://en.wikipedia.org/wiki/Differential_privacy)
* Privacy-preserving filtered aggregation of conversion data using [homomorphic encryption](https://en.wikipedia.org/wiki/Homomorphic_encryption)
