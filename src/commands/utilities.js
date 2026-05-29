const utilities = require('../modules/utilities');
const aiChat = require('../modules/aiChat');

const jokeCommand = async (ctx) => {
  try {
    await ctx.reply('⏳ Fetching a joke...');
    const joke = await utilities.getRandomJoke();
    await ctx.reply(`😄 *Random Joke*\n\n${joke}`);
  } catch (error) {
    console.error('Error in joke command:', error);
    await ctx.reply('❌ An error occurred. Please try again.');
  }
};

const countryCommand = async (ctx) => {
  try {
    const countryName = ctx.message.text.replace('/country ', '').trim();

    if (!countryName) {
      await ctx.reply('🌍 Usage: /country <country name>\nExample: /country France');
      return;
    }

    await ctx.reply('⏳ Fetching country info...');
    const countryInfo = await utilities.getCountryInfo(countryName);

    if (!countryInfo) {
      await ctx.reply(`❌ Country "${countryName}" not found.`);
      return;
    }

    const message = `
🌍 *${countryInfo.flag} ${countryInfo.name}*

📍 Capital: ${countryInfo.capital}
🗺️ Region: ${countryInfo.region}
👥 Population: ${countryInfo.population}
📐 Area: ${countryInfo.area} km²
⏰ Timezone: ${countryInfo.timezone}
💰 Currency: ${countryInfo.currency}
    `;

    await ctx.reply(message, { parse_mode: 'Markdown' });
  } catch (error) {
    console.error('Error in country command:', error);
    await ctx.reply('❌ An error occurred. Please try again.');
  }
};

const translateCommand = async (ctx) => {
  try {
    const text = ctx.message.text.replace('/translate ', '').trim();
    const parts = text.split(' ');
    const targetLanguage = parts[0];
    const textToTranslate = parts.slice(1).join(' ');

    if (!targetLanguage || !textToTranslate) {
      await ctx.reply('🌐 Usage: /translate <language> <text>\nExample: /translate Spanish Hello world');
      return;
    }

    await ctx.reply('⏳ Translating...');
    const translation = await aiChat.translate(textToTranslate, targetLanguage);

    if (!translation) {
      await ctx.reply('❌ Translation failed. Please try again.');
      return;
    }

    await ctx.reply(`
🌐 *Translation to ${targetLanguage}*

*Original:*
${textToTranslate}

*Translation:*
${translation}
    `, { parse_mode: 'Markdown' });
  } catch (error) {
    console.error('Error in translate command:', error);
    await ctx.reply('❌ An error occurred. Please try again.');
  }
};

const exchangeCommand = async (ctx) => {
  try {
    const text = ctx.message.text.replace('/exchange ', '').trim();
    const parts = text.split(' ');

    if (parts.length < 3) {
      await ctx.reply('💱 Usage: /exchange <from> <to> <amount>\nExample: /exchange USD EUR 100');
      return;
    }

    const from = parts[0].toUpperCase();
    const to = parts[1].toUpperCase();
    const amount = parseFloat(parts[2]);

    if (isNaN(amount)) {
      await ctx.reply('❌ Invalid amount. Please enter a number.');
      return;
    }

    await ctx.reply('⏳ Fetching exchange rate...');
    const rate = await utilities.getCurrencyExchange(from, to);

    if (!rate) {
      await ctx.reply(`❌ Could not fetch exchange rate for ${from} to ${to}.`);
      return;
    }

    const converted = (amount * rate).toFixed(2);
    const message = `
💱 *Currency Conversion*

${amount} ${from} = *${converted} ${to}*

📊 Exchange Rate: 1 ${from} = ${rate.toFixed(4)} ${to}
    `;

    await ctx.reply(message, { parse_mode: 'Markdown' });
  } catch (error) {
    console.error('Error in exchange command:', error);
    await ctx.reply('❌ An error occurred. Please try again.');
  }
};

module.exports = {
  jokeCommand,
  countryCommand,
  translateCommand,
  exchangeCommand,
};
