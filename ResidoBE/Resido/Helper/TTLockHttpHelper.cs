using Newtonsoft.Json;

namespace Resido.Helper
{
    public static class TTLockHttpHelper
    {
        private static readonly HttpClient _httpClient = new HttpClient();

        public static async Task<HttpResponseMessage> PostObjectWithResponseAsync<TRequest>(string url, TRequest request)
        {
            var formData = new FormUrlEncodedContent(
                request.GetType()
                       .GetProperties()
                       .ToDictionary(p => p.GetCustomAttributes(typeof(JsonPropertyAttribute), false)
                                           .Cast<JsonPropertyAttribute>()
                                           .FirstOrDefault()?.PropertyName ?? p.Name,
                                     p => p.GetValue(request)?.ToString() ?? string.Empty)
            );

            return await _httpClient.PostAsync(url, formData);
        }

        public static async Task<string> PostObjectAsync<TRequest>(string url, TRequest request)
        {
            var formData = new FormUrlEncodedContent(
                request.GetType()
                       .GetProperties()
                       .ToDictionary(p => p.GetCustomAttributes(typeof(JsonPropertyAttribute), false)
                                           .Cast<JsonPropertyAttribute>()
                                           .FirstOrDefault()?.PropertyName ?? p.Name,
                                     p => p.GetValue(request)?.ToString() ?? string.Empty)
            );

            var response = await _httpClient.PostAsync(url, formData);
            return await response.Content.ReadAsStringAsync();
        }
        /// <summary>
        /// Executes a GET request to the specified URL and returns the raw HttpResponseMessage.
        /// </summary>
        /// <param name="url">The full URL including query string.</param>
        /// <returns>HttpResponseMessage from the TTLock API.</returns>
        public static async Task<HttpResponseMessage> GetObjectWithResponseAsync(string url)
        {
            // TTLock APIs require application/x-www-form-urlencoded style query strings,
            // but for GET we just append them to the URL.
            var request = new HttpRequestMessage(HttpMethod.Get, url);

            // Optional: set headers if TTLock requires them
            request.Headers.Accept.Add(new System.Net.Http.Headers.MediaTypeWithQualityHeaderValue("application/json"));

            return await _httpClient.SendAsync(request);
        }

        public static async Task<HttpResponseMessage> GetAsync(string url)
        {
            return await _httpClient.GetAsync(url);
        }
    }

}
