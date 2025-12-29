using Newtonsoft.Json;

namespace Resido.Helper
{
    public static class TTLockHttpHelper
    {
        private static readonly HttpClient _httpClient = new HttpClient();

        /// <summary>
        /// Converts an object into FormUrlEncodedContent with camelCase keys.
        /// </summary>
        public static FormUrlEncodedContent BuildCamelCaseFormData<TRequest>(TRequest request)
        {
            var dict = request.GetType()
                              .GetProperties()
                              .ToDictionary(
                                  p =>
                                  {
                                      var jsonProp = p.GetCustomAttributes(typeof(JsonPropertyAttribute), false)
                                                      .Cast<JsonPropertyAttribute>()
                                                      .FirstOrDefault()?.PropertyName;

                                      var name = jsonProp ?? p.Name;
                                      return char.ToLowerInvariant(name[0]) + name.Substring(1);
                                  },
                                  p => p.GetValue(request)?.ToString() ?? string.Empty
                              );

            return new FormUrlEncodedContent(dict);
        }

        public static async Task<HttpResponseMessage> PostObjectWithResponseAsync<TRequest>(string url, TRequest request)
        {
            var formData = BuildCamelCaseFormData(request);

            string rawFormData = await formData.ReadAsStringAsync();
            Console.WriteLine($"POST {url} => {rawFormData}");

            return await _httpClient.PostAsync(url, formData);
        }

        public static async Task<string> PostObjectAsync<TRequest>(string url, TRequest request)
        {
            var formData = BuildCamelCaseFormData(request);

            var response = await _httpClient.PostAsync(url, formData);
            string responseBody = await response.Content.ReadAsStringAsync();

            Console.WriteLine($"Response: {response.StatusCode} => {responseBody}");
            return responseBody;
        }

        public static async Task<HttpResponseMessage> PostFormWithResponseAsync(string url, Dictionary<string, string> data)
        {
            var formData = new FormUrlEncodedContent(data);

            string rawFormData = await formData.ReadAsStringAsync();
            Console.WriteLine($"POST {url} => {rawFormData}");

            return await _httpClient.PostAsync(url, formData);
        }

        /// <summary>
        /// Executes a GET request with headers and returns HttpResponseMessage.
        /// </summary>
        public static async Task<HttpResponseMessage> GetObjectWithResponseAsync(string url)
        {
            var request = new HttpRequestMessage(HttpMethod.Get, url);
            request.Headers.Accept.Add(new System.Net.Http.Headers.MediaTypeWithQualityHeaderValue("application/json"));

            Console.WriteLine($"GET {url}");
            return await _httpClient.SendAsync(request);
        }

        /// <summary>
        /// Executes a simple GET request and returns HttpResponseMessage.
        /// </summary>
        public static async Task<HttpResponseMessage> GetAsync(string url)
        {
            Console.WriteLine($"GET {url}");
            return await _httpClient.GetAsync(url);
        }
    }


}
