using Resido.Model.TTLockDTO.RequestDTO;

namespace Resido.Model.TTLockDTO.RequestDTO.EkeysRq
{
    public class DeleteKeyRequestDTO : BaseRequestDTO, IAccessTokenRequest
    {
        public int KeyId { get; set; }
        public string AccessToken { get; set; }
    }
}
