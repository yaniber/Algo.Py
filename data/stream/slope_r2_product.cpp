/*
Compiled with : 
g++ -O3 -Wall -shared -std=c++17 -fPIC $(python3 -m pybind11 --includes) slope_r2_product.cpp -o slope_r2_product.so
*/
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <vector>
#include <numeric>
#include <cmath>
#include <stdexcept>
#include <algorithm>

namespace py = pybind11;

class SlopeR2Product {
public:
    std::vector<double> close_prices;

    explicit SlopeR2Product(std::vector<double> prices) : close_prices(std::move(prices)) {}

    std::vector<double> Normalize(const std::vector<double>& series) const {
        if (series.empty()) {
            throw std::invalid_argument("Input series cannot be empty");
        }
        double min_val = *std::min_element(series.begin(), series.end());
        double max_val = *std::max_element(series.begin(), series.end());
        if (min_val == max_val) {
            throw std::runtime_error("All values are identical, cannot normalize");
        }
        std::vector<double> normalized;
        for (const auto& val : series) {
            normalized.push_back((val - min_val) / (max_val - min_val));
        }
        return normalized;
    }

    std::vector<double> CreateXseries(size_t size) const {
        std::vector<double> x_vals(size);
        std::iota(x_vals.begin(), x_vals.end(), 1.0);
        return x_vals;
    }

    double CalcMean(const std::vector<double>& series) const {
        if (series.empty()) {
            throw std::invalid_argument("Input series cannot be empty");
        }
        return std::accumulate(series.begin(), series.end(), 0.0) / series.size();
    }

    double CalcVariance(const std::vector<double>& series, double mean) const {
        double variance = 0.0;
        for (const auto& value : series) {
            variance += (value - mean) * (value - mean);
        }
        return variance / series.size();
    }

    double CalcCovariance(const std::vector<double>& x, double x_mean,
                          const std::vector<double>& y, double y_mean) const {
        if (x.size() != y.size()) {
            throw std::invalid_argument("X and Y series must have the same size");
        }
        double covariance = 0.0;
        for (size_t i = 0; i < x.size(); ++i) {
            covariance += (x[i] - x_mean) * (y[i] - y_mean);
        }
        return covariance / x.size();
    }

    double CalcSlopeR2Product() const {
        auto normalized_prices = Normalize(close_prices);
        auto normalized_x = Normalize(CreateXseries(normalized_prices.size()));
        double x_mean = CalcMean(normalized_x);
        double y_mean = CalcMean(normalized_prices);
        double variance_x = CalcVariance(normalized_x, x_mean);
        double variance_y = CalcVariance(normalized_prices, y_mean);
        if (variance_x == 0 || variance_y == 0) {
            throw std::runtime_error("Variance is zero, cannot compute regression parameters");
        }
        double covariance = CalcCovariance(normalized_x, x_mean, normalized_prices, y_mean);
        double slope = covariance / variance_x;
        double correlation = covariance / (std::sqrt(variance_x) * std::sqrt(variance_y));
        return slope * (correlation * correlation);
    }
};

// Binding the C++ class to Python
PYBIND11_MODULE(slope_r2_product, m) {
    py::class_<SlopeR2Product>(m, "SlopeR2Product")
        .def(py::init<std::vector<double>>())
        .def("calc_slope_r2_product", &SlopeR2Product::CalcSlopeR2Product);
}
