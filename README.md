# Registered Interests Data Project

## Overview

This Django project is dedicated to downloading, processing, and displaying data on **registered interests** of UK Members of Parliament (MPs) and Members of the House of Lords. Data are sourced from the **UK Parliament API**.

## What are Registered Interests?

In the UK, **registered interests** refer to any enticements or other benefits that MPs and Lords are legally required to declare, including:

- **Donations**: Financial contributions from individuals or organisations.
- **Employment**: Jobs, consulting roles, or other paid work.
- **Family Connections**: Interests or relationships involving family members that could affect decision-making.
- **Land Ownership**: Ownership of land or property that could impact financial interests.
- **Shareholding**: Ownership of company shares or stock that may influence actions or decisions.
- **Other Financial Interests**: This could include directorships, memberships, or other financial benefits that might affect MPs' or Lords' actions.

These declarations help identify and address potential conflicts of interest in the legislative process.

## Limitations

- **Data Aggregation Issues**: Some data processing may be incomplete or imprecise as the source data is highly textual, and the extraction process prioritised speed. As this is a personal project, some inaccuracies or omissions may occur.
  
- **Incompleteness of Parliament API**: The UK Parliament API may not always provide comprehensive data. For example, Boris Johnson's registered interests can only be found deeper within Parliament's website as of writing. Essentially, some entries may be missing.

## Dependencies

- There are dependency files.
- Data for this project is sourced from the UK Parliament API. However, the raw JSON data files are **not included** in the repository to keep things light.
- The `.env` file, which contains sensitive information like the Django secret key and PostgreSQL credentials, has also **not been included**.
