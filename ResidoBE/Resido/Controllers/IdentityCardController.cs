using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Resido.BAL;
using Resido.Database;
using Resido.Database.DBTable;
using Resido.Helper.TokenAuthorize;
using Resido.Model.CommonDTO;
using Resido.Model.TTLockDTO.RequestDTO.CardRq;
using Resido.Model.TTLockDTO.ResponseDTO.CardRsp;
using Resido.Model.TTLockDTO.ResponseDTO.PasscodeRsp;
using Resido.Resources;
using Resido.Services;
using Resido.Services.DAL;

namespace Resido.Controllers
{
    [Route("api/[controller]/[action]")]
    [ApiController]
    [TokenAuthorize]
    public class IdentityCardController : BaseApiController
    {
        ResidoDbContext _context;
        CommonDBLogic _commonDBLogic;
        TTLockService _ttLockHelper;
        private readonly IServiceScopeFactory _serviceScopeFactory;
        public IdentityCardController(
                     ResidoDbContext context,
                     CommonDBLogic commonDBLogic,
                     TTLockService tTLockHelper,
                     IWebHostEnvironment env,
                     IServiceScopeFactory serviceScopeFactory
        ) : base(context)
        {
            _context = context;
            _commonDBLogic = commonDBLogic;
            _ttLockHelper = tTLockHelper;
            _serviceScopeFactory = serviceScopeFactory;
        }

        // POST: /api/IdentityCard/AddCard
        [HttpPost]
        [TokenAuthorize]
        public async Task<ActionResult<ResponseDTO<AddCardResponseDTO>>> AddCard([FromBody] AddCardRequestDTO dto, [FromQuery] bool useReversedApi = true)
        {
            var response = new ResponseDTO<AddCardResponseDTO>();
            response.SetFailed();

            try
            {
             

                var token = await GetAccessTokenEntityAsync();
                var smartLock = await _context.SmartLocks.FirstOrDefaultAsync(a => a.TTLockId == dto.LockId && a.UserId == token.UserId);

                if (smartLock == null)
                    return Ok(response.SetMessage(Resource.InvalidSmartLock));

                if (!token.IsValidAccessToken())
                    return Ok(response.SetMessage(Resource.InvalidAccessToken));

                var result = await _ttLockHelper.AddCardAsync(token.AccessToken, dto, useReversedApi);

                if (result.IsSuccessCode())
                {
                    Card card = new Card();

                    card.CardNumber = dto.CardNumber;
                    card.CardId = result.Data.CardId;
                    card.SmartLockId = smartLock.Id;
                    _context.Cards.Add(card);
                    _context.SaveChanges();

                    response.Data = result.Data;
                    response.SetSuccess();
                }
                else
                {
                    response.SetMessage(result?.Data?.Errmsg);
                }
            }
            catch (Exception ex)
            {
                response.SetMessage(ex.Message);
            }

            return Ok(response);
        }

        // GET: /api/IdentityCard/ListIdentityCards
        [HttpGet]
        [TokenAuthorize]
        public async Task<ActionResult<ResponseDTO<ListIdentityCardResponseDTO>>> ListIdentityCards([FromQuery] ListIdentityCardRequestDTO dto)
        {
            var response = new ResponseDTO<ListIdentityCardResponseDTO>();
            response.SetFailed();

            try
            {
                var token = await GetAccessTokenEntityAsync();
                if (!token.IsValidAccessToken())
                    return Ok(response.SetMessage(Resource.InvalidAccessToken));

                var result = await _ttLockHelper.ListIdentityCardsAsync(token.AccessToken, dto);

                if (result.IsSuccessCode())
                {
                    response.Data = result.Data;
                    if (response?.Data?.List?.Any() ?? false)
                    {
                        foreach (var eKeyRecordDTO in response.Data.List)
                        {
                            var range = CommonLogic.CheckExpiry(eKeyRecordDTO.EndDate, 1);
                            eKeyRecordDTO.IsExpired = range.IsExpired;
                            eKeyRecordDTO.IsExpiringSoon = range.IsExpiringSoon;
                        }
                    }
                    response.SetSuccess();
                }
                else
                {
                    response.SetMessage(result.Message);
                }
            }
            catch (Exception ex)
            {
                response.SetMessage(ex.Message);
            }

            return Ok(response);
        }

        // POST: /api/IdentityCard/DeleteCard
        [HttpPost]
        [TokenAuthorize]
        public async Task<ActionResult<ResponseDTO<DeleteCardResponseDTO>>> DeleteCard([FromBody] DeleteCardRequestDTO dto)
        {
            var response = new ResponseDTO<DeleteCardResponseDTO>();
            response.SetFailed();

            try
            {
                var token = await GetAccessTokenEntityAsync();
                if (!token.IsValidAccessToken())
                    return Ok(response.SetMessage(Resource.InvalidAccessToken));


                var result = await _ttLockHelper.DeleteCardAsync(token.AccessToken, dto);

                if (result.IsSuccessCode())
                {
                    Card? card = await _context.Cards.FirstOrDefaultAsync(a => a.CardId == dto.CardId);
                    if (card != null)
                    {
                        _context.Cards.Remove(card);
                        _context.SaveChanges();
                    }
                    response.Data = result.Data;
                    response.SetSuccess();
                }
                else
                {
                    response.SetMessage(result?.Data?.Errmsg);
                }
            }
            catch (Exception ex)
            {
                response.SetMessage(ex.Message);
            }

            return Ok(response);
        }

        // POST: /api/IdentityCard/ChangeCardPeriod
        [HttpPost]
        [TokenAuthorize]
        public async Task<ActionResult<ResponseDTO<ChangeCardPeriodResponseDTO>>> ChangeCardPeriod([FromBody] ChangeCardPeriodRequestDTO dto)
        {
            var response = new ResponseDTO<ChangeCardPeriodResponseDTO>();
            response.SetFailed();

            try
            {
                var token = await GetAccessTokenEntityAsync();
                if (!token.IsValidAccessToken())
                    return Ok(response.SetMessage(Resource.InvalidAccessToken));

                var result = await _ttLockHelper.ChangeCardPeriodAsync(token.AccessToken, dto);

                if (result.IsSuccessCode())
                {
                    response.Data = result.Data;
                    response.SetSuccess();
                }
                else
                {
                    response.SetMessage(result?.Data?.Errmsg);
                }
            }
            catch (Exception ex)
            {
                response.SetMessage(ex.Message);
            }

            return Ok(response);
        }

        // POST: /api/IdentityCard/ClearCard
        [HttpPost]
        [TokenAuthorize]
        public async Task<ActionResult<ResponseDTO<ClearCardResponseDTO>>> ClearCard([FromBody] ClearCardRequestDTO dto)
        {
            var response = new ResponseDTO<ClearCardResponseDTO>();
            response.SetFailed();

            try
            {
                var token = await GetAccessTokenEntityAsync();
                if (!token.IsValidAccessToken())
                    return Ok(response.SetMessage(Resource.InvalidAccessToken));

                var result = await _ttLockHelper.ClearCardAsync(token.AccessToken, dto);

                if (result.IsSuccessCode())
                {
                    var cards = await _context.Cards.Where(a => a.SmartLock.TTLockId == dto.LockId).ToListAsync();
                    if (cards != null)
                    {
                        _context.Cards.RemoveRange(cards);
                        _context.SaveChanges();
                    }
                    response.Data = result.Data;
                    response.SetSuccess();
                }
                else
                {
                    response.SetMessage(result?.Data?.Errmsg);
                }
            }
            catch (Exception ex)
            {
                response.SetMessage(ex.Message);
            }

            return Ok(response);
        }

        // POST: /api/IdentityCard/RenameCard
        [HttpPost]
        [TokenAuthorize]
        public async Task<ActionResult<ResponseDTO<RenameCardResponseDTO>>> RenameCard([FromBody] RenameCardRequestDTO dto)
        {
            var response = new ResponseDTO<RenameCardResponseDTO>();
            response.SetFailed();

            try
            {
                var token = await GetAccessTokenEntityAsync();
                if (!token.IsValidAccessToken())
                    return Ok(response.SetMessage(Resource.InvalidAccessToken));

                var result = await _ttLockHelper.RenameCardAsync(token.AccessToken, dto);

                if (result.IsSuccessCode())
                {
                    response.Data = result.Data;
                    response.SetSuccess();
                }
                else
                {
                    response.SetMessage(result?.Data?.Errmsg);
                }
            }
            catch (Exception ex)
            {
                response.SetMessage(ex.Message);
            }

            return Ok(response);
        }

    }
}
