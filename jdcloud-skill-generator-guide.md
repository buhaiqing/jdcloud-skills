# JD Cloud Skill Generator Guide

## 1. Introduction
The `jdcloud-skill-generator` is a Meta Skill designed to accelerate the creation of operational Agent Skills for JD Cloud products. It automates the extraction of product documentation and API definitions into a standardized Skill structure.

## 2. How to Use
To generate a new Skill, provide the following inputs to the generator:
- **Product Name**: e.g., "JD Cloud VM" or "JCS".
- **Documentation URL**: Link to the official JD Cloud product docs.
- **API Definition**: Swagger/OpenAPI file (optional but recommended).

### Example Prompt
> "Generate a JD Cloud Skill for 'Cloud Monitor'. Use the docs at [URL]. Focus on alarm configuration and metric retrieval."

## 3. Generated Structure
The generator will produce a directory with the following layout:
```
jdcloud-[product]-ops/
├── SKILL.md
├── references/
│   ├── core-concepts.md
│   ├── cli-usage.md
│   ├── troubleshooting.md
│   ├── monitoring.md
│   └── integration.md
└── assets/
    └── example-config.yaml
```

## 4. Customization
After generation, you should:
1. Verify CLI commands against the latest [JD Cloud CLI](https://github.com/jdcloud-api/jdcloud-cli) version.
2. Update IAM role examples in `integration.md`.
3. Add specific error codes to `troubleshooting.md` based on recent incidents.

### JD Cloud CLI GitHub Repository
- **Repository**: https://github.com/jdcloud-api/jdcloud-cli
- **Documentation**: https://docs.jdcloud.com/cn/cli/introduction
- **Installation**: `pip install jdcloud-cli` or download from [Releases](https://github.com/jdcloud-api/jdcloud-cli/releases)

## 5. Quality Checklist
- [ ] All placeholders (`[Product Name]`) are replaced.
- [ ] CLI commands include region and project ID parameters.
- [ ] Troubleshooting section covers top 5 common errors.
- [ ] Monitoring queries use correct metric namespaces.
