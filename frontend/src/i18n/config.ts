import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import ruTranslations from './locales/ru.json'
import kzTranslations from './locales/kz.json'

i18n
  .use(initReactI18next)
  .init({
    resources: {
      ru: { translation: ruTranslations },
      kz: { translation: kzTranslations },
    },
    lng: 'ru', // default language
    fallbackLng: 'ru',
    interpolation: {
      escapeValue: false,
    },
  })

export default i18n

