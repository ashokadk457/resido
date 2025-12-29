namespace Resido.Model.TTLockDTO.RequestDTO
{
    public class ListKeysRequestDTO : BaseRequestDTO, IAccessTokenRequest, IPagingRequest
    {
        public string AccessToken { get; set; }
        public string? LockAlias { get; set; }
        public int? GroupId { get; set; }
        public int PageNo { get; set; }
        public int PageSize { get; set; }
    }
}
