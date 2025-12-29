namespace Resido.Model.TTLockDTO.RequestDTO
{
    // Base request shared by all TTLock API calls
    public abstract class BaseRequestDTO
    {
        public string ClientId { get; set; }
        public string ClientSecret { get; set; }
        public string Date { get; set; }
    }

}
