using System.Net;
using System.Web;

namespace Resido.Helper.EmailHelper
{
    public static class EmailTemplates
    {

        public static (string Subject, string HtmlBody) BuildExistingUserEmailHtml(
    string recipientName,
    string username,
    string language = "en")
        {
            // Encode dynamic content for HTML safety
            string name = WebUtility.HtmlEncode(recipientName ?? "");
            string user = WebUtility.HtmlEncode(username ?? "");
            string lang = (language ?? "en").Trim().ToLowerInvariant();

            var langKey = (lang ?? "en").Trim().ToLowerInvariant();

            return langKey switch
            {
                "da-dk" => BuildExistingUserDanish(name, user),
                "nb" or "nb-no" => BuildExistingUserNorwegian(name, user),
                _ => BuildExistingUserEnglish(name, user)
            };
        }

        private static (string Subject, string HtmlBody) BuildExistingUserEnglish(string name, string user)
        {
            string subject = "You’ve received a new E-Key in ZafeLock";

            string html =
            $@"<!doctype html>
<html lang=""en"">
  <head>
    <meta charset=""utf-8"">
    <meta name=""viewport"" content=""width=device-width, initial-scale=1"">
    <title>{subject}</title>
  </head>
  <body style=""margin:0;padding:0;background:#f6f7f9;"">
    <div style=""max-width:640px;margin:24px auto;padding:0 16px;"">
      <div style=""background:#ffffff;border-radius:12px;box-shadow:0 1px 3px rgba(0,0,0,0.06);overflow:hidden;font-family:Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#222;"">
        <div style=""padding:24px 24px 8px 24px;"">
          <h1 style=""margin:0;font-size:20px;font-weight:600;"">You’ve received a new E-Key</h1>
        </div>

        <div style=""padding:0 24px 24px 24px;font-size:14px;line-height:1.6;"">
          <p style=""margin:16px 0;"">Dear {name},</p>

          <p style=""margin:16px 0;"">
            You have received a new E-Key in ZafeLock for access. Please log in using your existing account.
          </p>

          <div style=""margin:20px 0;padding:16px;border:1px solid #e6e8eb;border-radius:10px;background:#fafbfc;"">
            <div style=""font-weight:600;margin-bottom:8px;"">Account Details</div>
            <table role=""presentation"" cellpadding=""0"" cellspacing=""0"" style=""border-collapse:collapse;width:100%;font-size:14px;"">
              <tr>
                <td style=""padding:4px 0;width:120px;color:#555;"">Username:</td>
                <td style=""padding:4px 0;font-weight:600;"">{user}</td>
              </tr>
            </table>
          </div>

          <p style=""margin:16px 0;"">
            Download the ZafeLock app to access your E-Key:
          </p>

          <p>
            <a href=""https://apps.apple.com/in/app/zafe-connect/id6748814428"" style=""color:#007aff;text-decoration:none;margin-right:12px;"">App Store</a> |
            <a href=""https://play.google.com/store/apps/details?id=com.plento.zafelock"" style=""color:#34a853;text-decoration:none;margin-left:12px;"">Google Play</a>
          </p>

          <p style=""margin:16px 0;"">
            If you didn’t expect this, please contact our support team.
          </p>

          <p style=""margin:24px 0 0 0;"">Best regards,<br>ZafeLock Team</p>
        </div>
      </div>

      <p style=""text-align:center;color:#8a8f98;font-size:12px;margin:12px 0 0 0;font-family:Segoe UI,Roboto,Helvetica,Arial,sans-serif;"">
        © {DateTime.UtcNow:yyyy} ZafeLock
      </p>
    </div>
  </body>
</html>";

            return (subject, html);
        }

        private static (string Subject, string HtmlBody) BuildExistingUserDanish(string name, string user)
        {
            string subject = "Du har modtaget en ny E-nøgle i ZafeLock";

            string html =
            $@"<!doctype html>
<html lang=""da"">
  <head>
    <meta charset=""utf-8"">
    <meta name=""viewport"" content=""width=device-width, initial-scale=1"">
    <title>{subject}</title>
  </head>
  <body style=""margin:0;padding:0;background:#f6f7f9;"">
    <div style=""max-width:640px;margin:24px auto;padding:0 16px;"">
      <div style=""background:#ffffff;border-radius:12px;box-shadow:0 1px 3px rgba(0,0,0,0.06);overflow:hidden;font-family:Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#222;"">
        <div style=""padding:24px 24px 8px 24px;"">
          <h1 style=""margin:0;font-size:20px;font-weight:600;"">Du har modtaget en ny E-nøgle</h1>
        </div>

        <div style=""padding:0 24px 24px 24px;font-size:14px;line-height:1.6;"">
          <p style=""margin:16px 0;"">Kære {name},</p>

          <p style=""margin:16px 0;"">
            Du har modtaget en ny E-nøgle i ZafeLock til adgang. Log venligst ind med din eksisterende konto.
          </p>

          <div style=""margin:20px 0;padding:16px;border:1px solid #e6e8eb;border-radius:10px;background:#fafbfc;"">
            <div style=""font-weight:600;margin-bottom:8px;"">Kontooplysninger</div>
            <table role=""presentation"" cellpadding=""0"" cellspacing=""0"" style=""border-collapse:collapse;width:100%;font-size:14px;"">
              <tr>
                <td style=""padding:4px 0;width:120px;color:#555;"">Brugernavn:</td>
                <td style=""padding:4px 0;font-weight:600;"">{user}</td>
              </tr>
            </table>
          </div>

          <p style=""margin:16px 0;"">
            Download Zafe-appen for at få adgang til din E-nøgle:
          </p>

          <p>
            <a href=""https://apps.apple.com/in/app/zafe-connect/id6748814428"" style=""color:#007aff;text-decoration:none;margin-right:12px;"">App Store</a> |
            <a href=""https://play.google.com/store/apps/details?id=com.plento.zafelock"" style=""color:#34a853;text-decoration:none;margin-left:12px;"">Google Play</a>
          </p>

          <p style=""margin:16px 0;"">
            Hvis du ikke forventede dette, bedes du kontakte vores supportteam.
          </p>

          <p style=""margin:24px 0 0 0;"">Med venlig hilsen,<br>ZafeLock-teamet</p>
        </div>
      </div>

      <p style=""text-align:center;color:#8a8f98;font-size:12px;margin:12px 0 0 0;font-family:Segoe UI,Roboto,Helvetica,Arial,sans-serif;"">
        © {DateTime.UtcNow:yyyy} ZafeLock
      </p>
    </div>
  </body>
</html>";

            return (subject, html);
        }

        private static (string Subject, string HtmlBody) BuildExistingUserNorwegian(string name, string user)
        {
            string subject = "Du har mottatt en ny E-nøkkel i ZafeLock";

            string html =
        $@"<!doctype html>
<html lang=""nb"">
  <head>
    <meta charset=""utf-8"">
    <meta name=""viewport"" content=""width=device-width, initial-scale=1"">
    <title>{subject}</title>
  </head>
  <body style=""margin:0;padding:0;background:#f6f7f9;"">
    <div style=""max-width:640px;margin:24px auto;padding:0 16px;"">
      <div style=""background:#ffffff;border-radius:12px;box-shadow:0 1px 3px rgba(0,0,0,0.06);overflow:hidden;font-family:Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#222;"">
        <div style=""padding:24px 24px 8px 24px;"">
          <h1 style=""margin:0;font-size:20px;font-weight:600;"">Du har mottatt en ny E-nøkkel</h1>
        </div>

        <div style=""padding:0 24px 24px 24px;font-size:14px;line-height:1.6;"">
          <p style=""margin:16px 0;"">Hei {name},</p>

          <p style=""margin:16px 0;"">
            Du har mottatt en ny E-nøkkel i ZafeLock. Logg inn med din eksisterende konto.
          </p>

          <div style=""margin:20px 0;padding:16px;border:1px solid #e6e8eb;border-radius:10px;background:#fafbfc;"">
            <div style=""font-weight:600;margin-bottom:8px;"">Kontoopplysninger</div>
            <table role=""presentation"" cellpadding=""0"" cellspacing=""0"" style=""border-collapse:collapse;width:100%;font-size:14px;"">
              <tr>
                <td style=""padding:4px 0;width:120px;color:#555;"">Brukernavn:</td>
                <td style=""padding:4px 0;font-weight:600;"">{user}</td>
              </tr>
            </table>
          </div>

          <p style=""margin:16px 0;"">
            Last ned Zafe-appen for å få tilgang til din E-nøkkel:
          </p>

          <p>
            <a href=""https://apps.apple.com/in/app/zafe-connect/id6748814428"" style=""color:#007aff;text-decoration:none;margin-right:12px;"">App Store</a> |
            <a href=""https://play.google.com/store/apps/details?id=com.plento.zafelock"" style=""color:#34a853;text-decoration:none;margin-left:12px;"">Google Play</a>
          </p>

          <p style=""margin:16px 0;"">
            Hvis du ikke forventet dette, vennligst kontakt vårt supportteam.
          </p>

          <p style=""margin:24px 0 0 0;"">Med vennlig hilsen,<br>ZafeLock-teamet</p>
        </div>
      </div>

      <p style=""text-align:center;color:#8a8f98;font-size:12px;margin:12px 0 0 0;font-family:Segoe UI,Roboto,Helvetica,Arial,sans-serif;"">
        © {DateTime.UtcNow:yyyy} ZafeLock
      </p>
    </div>
  </body>
</html>";

            return (subject, html);
        }

        /// <summary>
        /// Builds the subject and HTML body for the ZafeLock welcome email in English or Danish.
        /// </summary>
        public static (string Subject, string HtmlBody) BuildWelcomeEmailHtml(
            string recipientName,
            string username,
            string password,
            string language = "en")
        {
            // Encode dynamic content for safety in HTML
            string name = WebUtility.HtmlEncode(recipientName ?? "");
            string user = WebUtility.HtmlEncode(username ?? "");
            string pass = WebUtility.HtmlEncode(password ?? "");
            string lang = (language ?? "en").Trim().ToLowerInvariant();

            var langKey = (lang ?? "en").Trim().ToLowerInvariant();
            return langKey switch
            {
                "da-dk" => BuildDanish(name, user, pass),
                "nb" or "nb-no" => BuildNorwegian(name, user, pass),
                _ => BuildEnglish(name, user, pass)
            };
        }

        private static (string Subject, string HtmlBody) BuildEnglish(string name, string user, string pass)
        {
            string subject = "Welcome to ZafeLock – Your account is ready";

            string html =
                    $@"<!doctype html>
                <html lang=""en"">
                  <head>
                    <meta charset=""utf-8"">
                    <meta name=""viewport"" content=""width=device-width, initial-scale=1"">
                    <title>{subject}</title>
                  </head>
                  <body style=""margin:0;padding:0;background:#f6f7f9;"">
                    <div style=""max-width:640px;margin:24px auto;padding:0 16px;"">
                      <div style=""background:#ffffff;border-radius:12px;box-shadow:0 1px 3px rgba(0,0,0,0.06);overflow:hidden;font-family:Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#222;"">
                        <div style=""padding:24px 24px 8px 24px;"">
                          <h1 style=""margin:0;font-size:20px;font-weight:600;"">Welcome to ZafeLock</h1>
                        </div>

                        <div style=""padding:0 24px 24px 24px;font-size:14px;line-height:1.6;"">
                          <p style=""margin:16px 0;"">Dear {name},</p>

                          <p style=""margin:16px 0;"">
                            Your Zafe account has been created, and we've sent you an eKey for access.
                          </p>

                          <div style=""margin:20px 0;padding:16px;border:1px solid #e6e8eb;border-radius:10px;background:#fafbfc;"">
                            <div style=""font-weight:600;margin-bottom:8px;"">Login Credentials</div>
                            <table role=""presentation"" cellpadding=""0"" cellspacing=""0"" style=""border-collapse:collapse;width:100%;font-size:14px;"">
                              <tr>
                                <td style=""padding:4px 0;width:120px;color:#555;"">Username:</td>
                                <td style=""padding:4px 0;font-weight:600;"">{user}</td>
                              </tr>
                              <tr>
                                <td style=""padding:4px 0;width:120px;color:#555;"">Password:</td>
                                <td style=""padding:4px 0;font-weight:600;"">{pass}</td>
                              </tr>
                            </table>
                          </div>

                          <p style=""margin:16px 0;"">Keep these details safe.</p>
                          <p style=""margin:16px 0;"">
                            You can manage your account and access settings via the Zafe platform.
                          </p>

                          <p style=""margin:16px 0;"">
                            Download the Zafe app to access your account:
                          </p>

                          <p>
                            <a href=""https://apps.apple.com/in/app/zafe-connect/id6748814428"" style=""color:#007aff;text-decoration:none;margin-right:12px;"">Download on App Store</a> |
                            <a href=""https://play.google.com/store/apps/details?id=com.plento.zafelock"" style=""color:#34a853;text-decoration:none;margin-left:12px;"">Get it on Google Play</a>
                          </p>

                          <p style=""margin:16px 0;"">
                            If you did not request this or need help, please contact our support team.
                          </p>

                          <p style=""margin:24px 0 0 0;"">Best regards,<br>ZafeLock Team</p>
                        </div>
                      </div>

                      <p style=""text-align:center;color:#8a8f98;font-size:12px;margin:12px 0 0 0;font-family:Segoe UI,Roboto,Helvetica,Arial,sans-serif;"">
                        © {DateTime.UtcNow:yyyy} ZafeLock
                      </p>
                    </div>
                  </body>
                </html>";
            return (subject, html);
        }

        private static (string Subject, string HtmlBody) BuildDanish(string name, string user, string pass)
        {
            string subject = "Velkommen til ZafeLock – Din konto er klar";

            string html =
    $@"<!doctype html>
<html lang=""da"">
  <head>
    <meta charset=""utf-8"">
    <meta name=""viewport"" content=""width=device-width, initial-scale=1"">
    <title>{subject}</title>
  </head>
  <body style=""margin:0;padding:0;background:#f6f7f9;"">
    <div style=""max-width:640px;margin:24px auto;padding:0 16px;"">
      <div style=""background:#ffffff;border-radius:12px;box-shadow:0 1px 3px rgba(0,0,0,0.06);overflow:hidden;font-family:Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#222;"">
        <div style=""padding:24px 24px 8px 24px;"">
          <h1 style=""margin:0;font-size:20px;font-weight:600;"">Velkommen til ZafeLock</h1>
        </div>

        <div style=""padding:0 24px 24px 24px;font-size:14px;line-height:1.6;"">
          <p style=""margin:16px 0;"">Kære {name},</p>

          <p style=""margin:16px 0;"">
            Din Zafe-konto er oprettet, og vi har sendt dig en eKey til adgang.
          </p>

          <div style=""margin:20px 0;padding:16px;border:1px solid #e6e8eb;border-radius:10px;background:#fafbfc;"">
            <div style=""font-weight:600;margin-bottom:8px;"">Loginoplysninger</div>
            <table role=""presentation"" cellpadding=""0"" cellspacing=""0"" style=""border-collapse:collapse;width:100%;font-size:14px;"">
              <tr>
                <td style=""padding:4px 0;width:120px;color:#555;"">Brugernavn:</td>
                <td style=""padding:4px 0;font-weight:600;"">{user}</td>
              </tr>
              <tr>
                <td style=""padding:4px 0;width:120px;color:#555;"">Adgangskode:</td>
                <td style=""padding:4px 0;font-weight:600;"">{pass}</td>
              </tr>
            </table>
          </div>

          <p style=""margin:16px 0;"">Opbevar disse oplysninger sikkert.</p>
          <p style=""margin:16px 0;"">
            Du kan administrere din konto og adgangsindstillinger via Zafe-platformen.
          </p>

          <p style=""margin:16px 0;"">
            Download Zafe-appen for at få adgang til din konto:
          </p>

          <p>
            <a href=""https://apps.apple.com/in/app/zafe-connect/id6748814428"" style=""color:#007aff;text-decoration:none;margin-right:12px;"">Hent i App Store</a> |
            <a href=""https://play.google.com/store/apps/details?id=com.plento.zafelock"" style=""color:#34a853;text-decoration:none;margin-left:12px;"">Hent på Google Play</a>
          </p>

          <p style=""margin:16px 0;"">
            Hvis du ikke har anmodet om dette eller har brug for hjælp, bedes du kontakte vores supportteam.
          </p>

          <p style=""margin:24px 0 0 0;"">Med venlig hilsen,<br>ZafeLock-teamet</p>
        </div>
      </div>

      <p style=""text-align:center;color:#8a8f98;font-size:12px;margin:12px 0 0 0;font-family:Segoe UI,Roboto,Helvetica,Arial,sans-serif;"">
        © {DateTime.UtcNow:yyyy} ZafeLock
      </p>
    </div>
  </body>
</html>";

            return (subject, html);
        }
        private static (string Subject, string HtmlBody) BuildNorwegian(string customerName, string email, string temporaryPassword)
        {
            string subject = "Velkommen til ZafeConnect – Din konto er klar";

            string html =
        $@"<!doctype html>
<html lang=""nb"">
  <head>
    <meta charset=""utf-8"">
    <meta name=""viewport"" content=""width=device-width, initial-scale=1"">
    <title>{subject}</title>
  </head>
  <body style=""margin:0;padding:0;background:#f6f7f9;"">
    <div style=""max-width:640px;margin:24px auto;padding:0 16px;"">
      <div style=""background:#ffffff;border-radius:12px;box-shadow:0 1px 3px rgba(0,0,0,0.06);overflow:hidden;font-family:Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#222;"">
        <div style=""padding:24px 24px 8px 24px;"">
          <h1 style=""margin:0;font-size:20px;font-weight:600;"">Velkommen til ZafeConnect</h1>
        </div>

        <div style=""padding:0 24px 24px 24px;font-size:14px;line-height:1.6;"">
          <p style=""margin:16px 0;"">Hei {customerName},</p>

          <p style=""margin:16px 0;"">
            Vi har gitt deg adgang med e-post: <strong>{email}</strong>.
          </p>

          <div style=""margin:20px 0;padding:16px;border:1px solid #e6e8eb;border-radius:10px;background:#fafbfc;"">
            <div style=""font-weight:600;margin-bottom:8px;"">Dine påloggingsopplysninger</div>
            <table role=""presentation"" cellpadding=""0"" cellspacing=""0"" style=""border-collapse:collapse;width:100%;font-size:14px;"">
              <tr>
                <td style=""padding:4px 0;width:120px;color:#555;"">E-post:</td>
                <td style=""padding:4px 0;font-weight:600;"">{email}</td>
              </tr>
              <tr>
                <td style=""padding:4px 0;width:120px;color:#555;"">Midlertidig passord:</td>
                <td style=""padding:4px 0;font-weight:600;"">{temporaryPassword}</td>
              </tr>
            </table>
          </div>

          <p style=""margin:16px 0;"">
            Last ned appen Zafe Connect i App Store eller Google Play, klikk på 'Glemt passord' for å tilbakestille passordet. Alternativt kan du endre passordet etter at du har logget inn.
          </p>

          <p style=""margin:24px 0 0 0;"">Med vennlig hilsen,<br>ZafeConnect-teamet</p>
        </div>
      </div>

      <p style=""text-align:center;color:#8a8f98;font-size:12px;margin:12px 0 0 0;font-family:Segoe UI,Roboto,Helvetica,Arial,sans-serif;"">
        © {DateTime.UtcNow:yyyy} ZafeConnect
      </p>
    </div>
  </body>
</html>";

            return (subject, html);
        }


        public static string GetCustomerAccessEmail(string customerName, string email, string temporaryPassword, string language = "en")
        {
            string appLinks = $@"
              <p>
                Download the Zafe app:
                <br>
                <a href=""https://apps.apple.com/in/app/zafe-connect/id6748814428"" style=""color:#007aff;text-decoration:none;"">App Store</a> |
                <a href=""https://play.google.com/store/apps/details?id=com.plento.zafelock"" style=""color:#34a853;text-decoration:none;"">Google Play</a>
              </p>";
            switch (language.ToLower())
            {
                case "da-dk": // Danish
                    return $@"<!DOCTYPE html>
<html>
<head>
  <meta charset=""utf-8"" />
  <title>Kundeadgang</title>
</head>
<body>
  <p>
    Hej, vi har givet adgang til kunden <strong>{customerName}</strong> til din e-mail: <strong>{email}</strong>.
  </p>

  <p>
    Du kan logge ind med følgende oplysninger:
  </p>
  <ul>
    <li><strong>Email:</strong> {email}</li>
    <li><strong>Midlertidig adgangskode:</strong> {temporaryPassword}</li>
  </ul>

  <p>
    Download Zafe-appen, klik på 'Glemt adgangskode', nulstil din adgangskode, eller efter login kan du ændre din adgangskode.
  </p>
  {appLinks}
</body>
</html>";
                case "nb-no": // Norwegian Bokmål
                case "nb": // Norwegian Bokmål
                    return $@"<!DOCTYPE html>
<html>
<head>
  <meta charset=""utf-8"" />
  <title>Kundeadgang</title>
</head>
<body>
  <p>
    Hei, vi har gitt kunden <strong>{customerName}</strong> adgang med e-post: <strong>{email}</strong>.
  </p>

  <p>
    Du kan logge inn med følgende opplysninger:
  </p>
  <ul>
    <li><strong>E-post:</strong> {email}</li>
    <li><strong>Midlertidig passord:</strong> {temporaryPassword}</li>
  </ul>

  <p>
    Last ned Zafe-appen, klikk på 'Glemt passord', og tilbakestill passordet ditt. 
    Alternativt kan du endre passordet etter at du har logget inn.
  </p>
  {appLinks}
</body>
</html>";
                case "en": // English (default)
                default:
                    return $@"<!DOCTYPE html>
<html>
<head>
  <meta charset=""utf-8"" />
  <title>Customer Access</title>
</head>
<body>
  <p>
    Hi, we have provided access for customer <strong>{customerName}</strong> to your email: <strong>{email}</strong>.
  </p>

  <p>
    You can log in using the following details:
  </p>
  <ul>
    <li><strong>Email:</strong> {email}</li>
    <li><strong>Temporary Password:</strong> {temporaryPassword}</li>
  </ul>

  <p>
    Download the Zafe app, click on 'Forgot Password', reset your password, or after login you can reset your password.
  </p>
  {appLinks}
</body>
</html>";
            }
        }
        public static string GetCustomerInviteEmail(string customerName, string email, string language = "en")
        {
            string appLinks = $@"
      <p>
        Download the Zafe app:
        <br>
        <a href=""https://apps.apple.com/in/app/zafe-connect/id6748814428"" style=""color:#007aff;text-decoration:none;"">App Store</a> |
        <a href=""https://play.google.com/store/apps/details?id=com.plento.zafelock"" style=""color:#34a853;text-decoration:none;"">Google Play</a>
      </p>";

            switch (language.ToLower())
            {
                case "da-dk": // Danish
                    return $@"<!DOCTYPE html>
<html>
<head>
  <meta charset=""utf-8"" />
  <title>Kundeinvitation</title>
</head>
<body>
  <p>
    Hej <strong>{customerName}</strong>,
  </p>

  <p>
    Du er blevet inviteret til at få adgang med e-mailen <strong>{email}</strong>.
  </p>

  <p>
    Åbn venligst Zafe-appen og log ind med din eksisterende konto.
    Hvis du ikke kan huske din adgangskode, skal du trykke på 'Glemt adgangskode' for at nulstille den.
  </p>

  {appLinks}
</body>
</html>";
                case "nb":      // Norwegian Bokmål
                case "nb-no":   // Norwegian Bokmål with region
                    return $@"<!DOCTYPE html>
<html>
<head>
  <meta charset=""utf-8"" />
  <title>Kundeinvitasjon</title>
</head>
<body>
  <p>
    Hei <strong>{customerName}</strong>,
  </p>

  <p>
    Du er invitert til å få tilgang til kontoen din med e-post <strong>{email}</strong>.
  </p>

  <p>
    Åpne Zafe-appen og logg inn med din eksisterende konto.
    Hvis du ikke husker passordet ditt, trykk på 'Glemt passord' for å tilbakestille det.
  </p>

  {appLinks}
</body>
</html>";
                case "en": // English (default)
                default:
                    return $@"<!DOCTYPE html>
<html>
<head>
  <meta charset=""utf-8"" />
  <title>Customer Invitation</title>
</head>
<body>
  <p>
    Hi <strong>{customerName}</strong>,
  </p>

  <p>
    You’ve been invited to access your account using the email <strong>{email}</strong>.
  </p>

  <p>
    Please open the Zafe app and log in using your existing account.
    If you don’t remember your password, tap on 'Forgot Password' to reset it.
  </p>

  {appLinks}
</body>
</html>";
            }
        }

    }
    public static class SmsContentHelper
    {

        public static async Task<string> GetSmsContentAsync(string language, string username, string password)
        {
            string shortIos = await TryShortenUrlAsync(ApplicationDefaults.AppStoreLink);
            string shortAndroid = await TryShortenUrlAsync(ApplicationDefaults.PlayStoreLink);

            switch (language?.ToLower())
            {
                case "da-dk": // Danish
                    return $"ZafeLock klar!\nBruger: {username}\nKode: {password}\nApp: iOS {shortIos} | Android {shortAndroid}";
                case "nb":      // Norwegian Bokmål
                case "nb-no":
                    return $"ZafeLock klar!\nBruker: {username}\nPassord: {password}\nApp: iOS {shortIos} | Android {shortAndroid}";
                case "en": // English
                default:
                    return $"ZafeLock ready!\nUser: {username}\nPass: {password}\nApp: iOS {shortIos} | Android {shortAndroid}";
            }
        }
        public static async Task<string> GetSmsContentForExistingUserAsync(string language, string username)
        {
            string shortIos = await TryShortenUrlAsync(ApplicationDefaults.AppStoreLink);
            string shortAndroid = await TryShortenUrlAsync(ApplicationDefaults.PlayStoreLink);

            switch (language?.ToLower())
            {
                case "da-dk": // Danish
                    return $"Du har modtaget en E-nøgle i ZafeLock.\nBruger: {username}\nApp: iOS {shortIos} | Android {shortAndroid}";
                case "nb":
                case "nb-no":
                    return $"Du har mottatt en E-nøkkel i ZafeLock.\nBruker: {username}\nApp: iOS {shortIos} | Android {shortAndroid}";
                case "en": // English
                default:
                    return $"You have received an E-Key in ZafeLock.\nUser: {username}\nApp: iOS {shortIos} | Android {shortAndroid}";
            }
        }

        public static async Task<string> GetSmsContentForUserInvitationWithPasswordAsync(
    string language,
    string username,
    string tempPassword)
        {
            string shortIos = await TryShortenUrlAsync(ApplicationDefaults.AppStoreLink);
            string shortAndroid = await TryShortenUrlAsync(ApplicationDefaults.PlayStoreLink);

            switch (language?.ToLower())
            {
                case "da-dk": // Danish
                    return
                        $"Du er blevet inviteret til ZafeConnect.\n" +
                        $"Bruger: {username}\n" +
                        $"Midlertidig adgangskode: {tempPassword}\n" +
                        $"Download appen:\n" +
                        $"iOS: {shortIos} | Android: {shortAndroid}";
                case "nb":
                case "nb-no":
                    return
                        $"Du er invitert til ZafeConnect.\n" +
                        $"Bruker: {username}\n" +
                        $"Midlertidig passord: {tempPassword}\n" +
                        $"Last ned appen:\n" +
                        $"iOS: {shortIos} | Android: {shortAndroid}";
                case "en": // English
                default:
                    return
                        $"You have been invited to ZafeConnect.\n" +
                        $"User: {username}\n" +
                        $"Temporary Password: {tempPassword}\n" +
                        $"Download the app:\n" +
                        $"iOS: {shortIos} | Android: {shortAndroid}";
            }
        }

        public static async Task<string> GetSmsContentForUserInvitationWithoutPasswordAsync(
    string language,
    string username)
        {
            string shortIos = await TryShortenUrlAsync(ApplicationDefaults.AppStoreLink);
            string shortAndroid = await TryShortenUrlAsync(ApplicationDefaults.PlayStoreLink);

            switch (language?.ToLower())
            {
                case "da-dk": // Danish
                    return
                        $"Du har fået adgang til ZafeConnect.\n" +
                        $"Bruger: {username}\n" +
                        $"Download appen:\n" +
                        $"iOS: {shortIos} | Android: {shortAndroid}";
                case "nb":
                case "nb-no":
                    return
                        $"Du har fått tilgang til ZafeConnect.\n" +
                        $"Bruker: {username}\n" +
                        $"Last ned appen:\n" +
                        $"iOS: {shortIos} | Android: {shortAndroid}";
                case "en": // English
                default:
                    return
                        $"You have been granted access to ZafeConnect.\n" +
                        $"User: {username}\n" +
                        $"Download the app:\n" +
                        $"iOS: {shortIos} | Android: {shortAndroid}";
            }
        }


        private static async Task<string> TryShortenUrlAsync(string url)
        {
            try
            {
                using var client = new HttpClient();
                string encoded = HttpUtility.UrlEncode(url);
                string apiUrl = $"https://tinyurl.com/api-create.php?url={encoded}";

                var response = await client.GetStringAsync(apiUrl);
                if (!string.IsNullOrWhiteSpace(response) && response.StartsWith("http", StringComparison.OrdinalIgnoreCase))
                    return response.Trim();
            }
            catch
            {
                // Log exception if needed
            }

            // fallback to full URL if shortening fails
            return url;
        }
    }
}
