const axios = require('axios');

class UtilitiesManager {
  constructor() {
    this.jokeUrl = 'https://icanhazdadjoke.com/json';
    this.countriesUrl = 'https://restcountries.com/v3.1';
  }

  async getRandomJoke() {
    try {
      const response = await axios.get(this.jokeUrl);
      return response.data.joke;
    } catch (error) {
      console.error('❌ Error fetching joke:', error.message);
      return '😄 Why did the bot cross the road? To get to the other API!';
    }
  }

  async getCountryInfo(countryName) {
    try {
      const response = await axios.get(`${this.countriesUrl}/name/${countryName}`);
      const country = response.data[0];

      return {
        name: country.name.common,
        capital: country.capital?.[0] || 'N/A',
        region: country.region,
        population: country.population?.toLocaleString(),
        area: country.area?.toLocaleString(),
        timezone: country.timezones?.[0] || 'N/A',
        currency: Object.values(country.currencies || {})[0]?.name || 'N/A',
        flag: country.flag,
      };
    } catch (error) {
      console.error('❌ Error fetching country info:', error.message);
      return null;
    }
  }

  async getAllCountries() {
    try {
      const response = await axios.get(`${this.countriesUrl}/all?fields=name,flag`);
      return response.data.map(c => ({ name: c.name.common, flag: c.flag }));
    } catch (error) {
      console.error('❌ Error fetching countries:', error.message);
      return [];
    }
  }

  async getCurrencyExchange(fromCurrency, toCurrency) {
    try {
      const response = await axios.get(
        `https://api.exchangerate-api.com/v4/latest/${fromCurrency}`
      );
      const rate = response.data.rates[toCurrency];
      return rate || null;
    } catch (error) {
      console.error('❌ Error fetching exchange rate:', error.message);
      return null;
    }
  }
}

module.exports = new UtilitiesManager();
