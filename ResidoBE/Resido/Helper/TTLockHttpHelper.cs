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

        public static async Task<HttpResponseMessage> GetAsync(string url)
        {
            return await _httpClient.GetAsync(url);
        }
    }

}
