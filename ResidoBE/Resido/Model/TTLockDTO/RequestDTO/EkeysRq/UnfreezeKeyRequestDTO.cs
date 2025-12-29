namespace Resido.Model.TTLockDTO.RequestDTO.EkeysRq
{
    public class UnfreezeKeyRequestDTO : BaseRequestDTO, IAccessTokenRequest
    {
        /// <summary>
        /// Ekey ID to unfreeze
        /// </summary>
        public int KeyId { get; set; }

        /// <summary>
        /// Access token for the current user
        /// </summary>
        public string AccessToken { get; set; }
    }
}
