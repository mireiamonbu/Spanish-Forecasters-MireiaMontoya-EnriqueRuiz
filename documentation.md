# Documentation – Daily Electricity Generation Forecasting (REE)

## 1. Business Problem

Electricity generation must be continuously balanced with demand to ensure grid stability. In power systems with a high share of renewable energy sources, generation becomes increasingly volatile and difficult to predict.

The objective of this project is to produce accurate daily forecasts of electricity generation by technology in Spain. These forecasts support operational and planning decisions such as activating backup generation, scheduling maintenance, managing imports and exports, and evaluating potential risks in the power system when future generation is uncertain.

## 2. Data Source

The data comes from **Red Eléctrica de España (REE)**, the Spanish Electric Network operator. The dataset is open, public, and updated regularly.

- Frequency: Daily
- Period: 2018–2025
- Granularity: Electricity generation by technology
- Nature: Dynamic open dataset

## 3. Data Engineering and Preparation

Raw data was initially provided as multiple yearly CSV files (2018–2025). The following steps were applied to construct the final modelling dataset:

- All yearly files were merged into a single dataset
- Technologies were ranked by average daily generation
- The top-7 technologies were selected to focus on the most relevant sources
- A complete daily date grid was created for each technology
- Missing values were filled using forward and backward filling
- The final dataset was structured as a balanced panel with columns:
  `[unique_id, ds, y]`

The resulting dataset is suitable for both univariate and global forecasting models.

## 4. Exploratory Data Analysis REVISAR

Exploratory analysis revealed strong temporal patterns and heterogeneity across technologies:

- Clear weekly seasonality in daily generation
- Long-term trends varying by technology
- Different volatility profiles across renewable and non-renewable sources

When looking at total electricity generation, we observe a generally stable pattern over time with noticeable daily and weekly fluctuations. This combination motivates the use of both traditional statistical models and more flexible machine learning approaches.

Visualizations of individual series and total generation were used to assess stationarity, seasonality, and potential structural changes.

## 5. Feature Engineering

Different feature sets were tested depending on the model family:

### Baseline and Statistical Models
- No explicit feature engineering
- Models rely on historical values and internal dynamics

### Machine Learning Models
- Lag features: 1, 2, 7, and 14 days
- Calendar features: day of week, day of month, and month
- Statistical lag transformations:
  - Rolling means
  - Expanding means

### Deep Learning Models
- Fixed input windows capturing recent historical patterns
- No manual feature engineering, allowing the models to learn representations directly from the data

## 6. Model Training

Models were grouped into four families:

- **Baselines:** naive forecast and moving average
- **Statistical:** AutoARIMA with weekly seasonality
- **Machine Learning:** Random Forest and Gradient Boosting using MLForecast
- **Deep Learning:** NBEATS and NLinear using NeuralForecast

A time-based split was used:
- Training set: all data except the last 62 days
- Validation set: 31 days
- Test set: final 31 days

Models were trained globally across all technologies where applicable, enabling them to share information across series.

## 7. Evaluation and Model Selection

Model performance was evaluated using multiple metrics:

- Mean Absolute Error (MAE)
- Root Mean Squared Error (RMSE)
- Mean Absolute Percentage Error (MAPE)
- Overall Percentage Error (OPE)
- R2 score

MAE on the validation set was used as the primary selection criterion due to its interpretability and robustness.

For each model family, the best-performing model was selected based on validation MAE. The final model was chosen as the one with the lowest average validation MAE across all technologies, excluding baseline models to ensure realistic forecasting behavior.

## 8. Final Forecast Composition

The selected best overall model was retrained using all available data (2018–2025). 
Daily forecasts were generated for January 2026.

Uncertainty was quantified using empirical prediction intervals derived from validation residuals. The 2.5% and 97.5% quantiles of the residual distribution were added to the point forecasts to obtain 95% prediction intervals.

The final outputs include:
- Point forecasts per technology
- Lower and upper 95% prediction bounds
- Aggregated total generation forecasts

All predictions and evaluation metrics were saved in reproducible CSV and Parquet formats.

## 9. Limitations and Future Work

- Prediction intervals are based on historical residuals and do not account for structural changes or extreme events
- Demand-side information was not included
- Exogenous variables such as weather could further improve accuracy

Future work could include probabilistic forecasting methods, weather-driven models, and longer forecasting horizons.

## 10. Reproducibility

The full forecasting pipeline is implemented using open-source libraries. All data processing, modelling, evaluation, and forecasting steps are fully reproducible through the provided code and documentation.
