# -*- coding: utf-8 -*-
# 장면/컷 데이터 -> 대본 + 스토리보드 + 업로드 정보 자동 생성. 시간은 음절 수 기준(분당 290음절)으로 계산.
SPM = 290
STYLE_PHOTO = "photorealistic, cinematic documentary style, 16:9, muted natural color grade, no text, no watermark"
STYLE_INFO = "clean flat infographic style, dark navy background, soft glow accents, 16:9, no text"

# (장면 제목, [ (대본, 화면 구성, 자막, 이미지 프롬프트, 스타일) ])
S = []

S.append(("훅", [
("미국에서 온 친구가 한국 지도를 한참 보다가 이렇게 물었어요. 이 나라는 왜 이렇게 작은데 이렇게 많은 게 들어 있냐고.",
 "카페 테이블 위 펼쳐진 한국 지도, 외국인 손이 지도를 가리킴, 얼굴은 프레임 밖", "자막 없음",
 "Close-up of a foreign traveler's hand pointing at a paper map of South Korea spread on a wooden cafe table, coffee cup beside, warm window light, shallow depth of field", "P"),
("저는 그때 웃으면서 넘겼어요. 그냥 외국인이 하는 덕담이라고 생각했거든요. 그런데 이 영상을 준비하면서 자료를 하나씩 찾아보다가 알게 됐습니다. 그 친구 말이 그냥 덕담이 아니었다는 걸요.",
 "화면 검게 전환, 질문 문장만 흰 글씨로 타이핑 효과", "왜 이렇게 작은데 이렇게 많은 게 들어 있어?",
 "Pure black background with a single thin white horizontal line of light in the center, minimalist, cinematic void, subtle film grain", "P"),
("한반도 남쪽, 딱 10만 제곱킬로미터. 세계에서 109번째 크기예요. 미국의 백분의 일도 안 되는 땅입니다. 서울에서 부산까지 KTX로 두 시간 반이면 가는 나라예요.",
 "미국 지도 위에 한반도 남쪽이 작게 얹혀 크기 비교, 숫자 카운터", "100,363제곱킬로미터, 세계 109위, 미국의 100분의 1",
 "Flat map comparison, outline of the continental United States in dim gray with a tiny glowing outline of South Korea placed over Texas for scale", "I"),
("그런데 이 땅에, 미국이 대륙 전체에 펼쳐놓은 것들이 한 번에 들어가 있습니다. 오늘은 우리가 매일 밟고 있는데도 한 번도 제대로 계산해 본 적 없는 이 땅의 진짜 가치를 숫자로 따져 보겠습니다.",
 "한반도 3D 지형도가 어둠에서 떠오르고 산맥, 강, 해안선이 차례로 켜짐", "국토의 진짜 가치",
 "Glowing 3D relief map of South Korea rising from darkness, mountain ranges, rivers and coastline lighting up in sequence, cinematic top-down angle", "I"),
("산, 물, 세 개의 바다, 그리고 갯벌. 이 순서로 갈 거예요. 그리고 마지막에 반전이 하나 있습니다. 제목에 신이 편애했다고 써놨는데, 사실 그 말은 절반만 맞아요. 나머지 절반은 끝까지 보시면 알아요.",
 "산, 물, 바다, 갯벌 아이콘 네 개가 순서대로 켜지고 마지막에 물음표", "산 / 물 / 세 바다 / 갯벌 / 그리고 반전",
 "Four minimal glowing icons in a row, mountain, water drop, wave, and mud flat texture, with a question mark appearing at the end", "I"),
]))

S.append(("산, 없던 숲을 만든 나라", [
("먼저 산부터 갈게요. 우리나라 국토의 63퍼센트가 숲입니다. 629만 헥타르. OECD 국가 중에 4위예요. 핀란드, 스웨덴, 일본 다음이 우리예요.",
 "울창한 산맥 드론 광각, 오른쪽에 63퍼센트 원형 게이지, OECD 순위 4개 국기", "산림 63퍼센트, OECD 4위",
 "Aerial drone view over endless layers of dense green Korean mountain ridges at early morning, thin mist between valleys", "P"),
("그런데 이게 원래 이랬던 게 아니에요. 1953년, 전쟁이 끝난 직후 사진을 보면 산이 다 벌거숭이예요. 일제강점기에 수탈당하고, 전쟁 때 불타고, 남은 나무는 땔감으로 다 베어 썼거든요. 겨울에 난방을 하려면 나무밖에 없었으니까요.",
 "흑백 톤, 나무 없는 민둥산과 지게 진 사람들", "1953년",
 "Black and white 1950s style photograph of barren eroded Korean hills with no trees, a few villagers carrying firewood bundles on wooden A-frame backpacks, dusty path, archival film grain", "P"),
("그때 우리 산에 서 있던 나무의 양을 1이라고 치면, 지금은 29입니다. 29배예요. 헥타르당 나무 부피로 따지면 165세제곱미터인데, OECD 평균이 131이에요. 우리가 평균을 넘어섰다는 거예요.",
 "같은 산의 좌우 분할, 왼쪽 1953 민둥산, 오른쪽 현재 숲. 숫자 1이 29로 커지고 이어서 막대그래프 165 대 131", "1 → 29 / 한국 165, OECD 평균 131",
 "Split-screen before and after of the same Korean hillside, left half barren brown eroded slope in faded sepia, right half the identical slope covered in thick green pine forest today, seamless center line", "P"),
("어떻게 했을까요. 1973년에 정부가 치산녹화 10개년 계획이라는 걸 세웁니다. 목표는 딱 하나, 전 국토의 녹화. 산림청을 내무부 밑으로 옮겨서 전국 행정조직을 전부 나무 심는 데 동원했어요.",
 "1970년대 관공서 벽에 붙은 녹화 포스터 느낌의 그래픽, 지도 위에 조림 구역이 퍼져 나감", "1973년, 치산녹화 10개년 계획",
 "1970s Korean government propaganda poster style illustration of citizens planting trees on a hillside, bold retro colors, slightly faded paper texture", "P"),
("그리고 진짜 중요한 걸 같이 했어요. 연탄이에요. 나무를 못 베게 막기만 하면 사람들은 얼어 죽어요. 그래서 무연탄을 대량으로 캐서 농촌까지 보급했어요. 땔감이 필요 없어지니까 산이 살아난 거예요.",
 "연탄 쌓인 골목, 연탄 배달 리어카, 아궁이에 연탄 넣는 손", "무연탄 보급, 땔감 수요 소멸",
 "Stacks of black cylindrical Korean coal briquettes with holes, piled in a narrow 1970s alley, a delivery cart, soft winter light", "P"),
("10년 계획이었는데 6년 만인 1978년에 목표를 넘겼어요. 108만 헥타르에 나무를 심었습니다. 1973년부터 2013년까지 심은 나무를 다 합치면 65억 그루예요. 국민 한 사람당 130그루씩 심은 셈이에요.",
 "수백 명이 산비탈에 줄지어 묘목 심는 모습, 카운터 65억", "1978년 조기 달성, 108만 헥타르, 65억 그루",
 "Hundreds of people in 1970s Korean work clothes planting tiny pine seedlings in neat rows across a bare hillside, wide shot, overcast sky, documentary photograph feel", "P"),
("유엔 식량농업기구가 이렇게 평가했어요. 2차 세계대전 이후 황폐해진 산림을 완전히 복구한 나라는 지구상에 한국 하나뿐이라고. 미국도 러시아도 숲이 넓죠. 근데 그건 원래 있던 거고요. 우리는 없던 걸 만들어낸 거예요. 이 차이는 뒤에서 다시 얘기할 거니까 기억해 두세요.",
 "카메라가 숲 위로 상승, 세계지도에 한국만 초록으로 켜짐", "전후 산림 복구 성공, 세계 유일",
 "Camera rising above a thick green Korean pine forest canopy into golden morning light, endless ridgelines behind", "P"),
]))

S.append(("물, 20억 년 화강암이 걸러낸 물", [
("다음은 물이에요. 우리나라 연평균 강수량이 1,300밀리미터입니다. 세계 평균의 1.6배예요. 비가 많이 오는 나라예요.",
 "장마철 산에 비 쏟아지는 슬로모션, 빗줄기 위로 숫자", "연 1,300밀리미터, 세계 평균 1.6배",
 "Heavy monsoon rain falling on a misty Korean mountain forest, slow motion raindrops, dark green foliage glistening, moody atmospheric light", "P"),
("그리고 이 비가 화강암과 편마암 위로 떨어져요. 한반도의 기반암 중에는 20억 년 가까이 된 아주 오래되고 단단한 암석이 있는데, 이게 천연 필터 역할을 해요. 빗물이 바위 틈을 천천히 지나면서 걸러지는 거예요.",
 "화강암 절벽 클로즈업, 바위 틈으로 물이 스며들어 나오는 매크로", "화강암, 편마암, 약 20억 년",
 "Extreme close-up of pale granite rock face with crystal clear water seeping through a crack and dripping, moss patches, sunlight catching each droplet, macro photography", "P"),
("그래서 우리나라 산에서 나오는 물이 그냥 마셔도 될 정도로 깨끗한 거예요. 산마다 약수터가 있는 나라, 생각보다 흔하지 않습니다. 유럽 여행 가서 수돗물 석회 때문에 고생해 본 분들은 아실 거예요.",
 "산속 약수터, 바가지로 물 받아 마시는 손. 짧게 유럽 세면대의 석회 자국 인서트", "산마다 약수터",
 "Traditional Korean mountain spring with water flowing from a stone spout into a small basin, a hand holding a wooden ladle catching the water, dappled forest light", "P"),
("여기서 하나 바로잡을게요. 인터넷에 한국 수돗물 UN 세계 8위라는 말이 많이 돌아요. 이거 정확하지 않습니다. 2003년 유네스코 보고서에 나온 수질 관리 종합 순위고, 마시는 물 순위가 아니에요. 20년도 더 된 자료예요. 이 영상에서는 확인된 것만 말씀드릴게요.",
 "인터넷 게시글 캡처 느낌의 그래픽에 빨간 취소선, 2003 보고서 표지 이미지", "수돗물 UN 8위? 2003년 수질관리 종합 순위, 마시는 물 순위 아님",
 "Stylized illustration of an old paper report cover stamped with the year 2003, a red diagonal line across a viral social media post graphic", "I"),
]))

S.append(("자리, 사계절과 조용한 땅", [
("이 땅이 어디에 놓여 있는지도 봐야 해요. 한반도는 중위도 온대 기후대에 있어요. 봄 여름 가을 겨울이 다 뚜렷하죠. 이게 당연한 게 아니에요. 지구상에 사계절이 이렇게 또렷한 땅은 생각보다 좁은 띠 안에만 있어요.",
 "같은 산의 사계절 4분할, 이어서 지구 위 온대 띠 하이라이트", "중위도 온대, 사계절",
 "Four-panel grid of the same Korean mountain village in spring blossoms, summer green, autumn red maples, and winter snow, matching camera angle", "P"),
("그리고 재해요. 독일 구호단체가 매년 193개 나라의 자연재해 위험도를 계산해서 발표하는 세계위험지수라는 게 있어요. 지진, 태풍, 홍수, 가뭄 위험을 다 합친 거예요.",
 "세계지도 위험도 색상 지도, 붉은색에서 초록색 그라데이션", "세계위험지수, 193개국",
 "World map heat-map of disaster risk, deep red high-risk zones in Southeast Asia fading to cool green low-risk regions", "I"),
("1위가 필리핀이에요. 4년 연속이요. 옆 나라 일본은 17위, 미국은 21위. 한국은요, 49위예요. 화산도 없고, 환태평양 지진대에서도 벗어나 있어요. 한반도는 유라시아판 안쪽에 있거든요.",
 "순위표 애니메이션 필리핀 1, 일본 17, 미국 21, 한국 49. 이어서 판 경계 지도에서 한반도가 판 안쪽에 위치", "필리핀 1위, 일본 17위, 미국 21위, 한국 49위",
 "Tectonic plate map of East Asia with the Pacific Ring of Fire glowing red along Japan and the Philippines, the Korean Peninsula sitting calmly inside the Eurasian plate", "I"),
("태풍은 오지만 필리핀이나 일본이 한 번 걸러준 뒤에 와요. 물론 홍수랑 폭우는 있어요. 그래도 이웃 나라들이랑 비교하면 확실히 조용한 자리예요. 이것도 뒤에서 한 번 더 다룰게요.",
 "위성 태풍 경로 지도, 필리핀과 일본을 지나 약해지며 한반도 접근", "이웃이 먼저 걸러주는 자리",
 "Satellite view of a massive typhoon spiraling over the western Pacific, its path curving past the Philippines and Japan toward Korea, dramatic cloud swirl", "P"),
]))

S.append(("동해, 미니 대양", [
("이제 바다로 가볼게요. 여기서부터가 진짜예요. 우리나라는 삼면이 바다잖아요. 그건 다 아는데, 이 세 바다가 완전히 다른 바다라는 건 잘 모르시죠.",
 "한반도 지도, 동해 서해 남해가 서로 다른 색으로 물듦", "동해, 서해, 남해",
 "Map of the Korean Peninsula surrounded by three seas each tinted a distinctly different shade, deep indigo east, pale turquoise west, teal south", "I"),
("동해요. 평균 수심이 1,684미터예요. 가장 깊은 곳은 3,762미터. 서울 남산을 열세 개 쌓아도 안 닿아요. 동해 바닷물의 89퍼센트가 수심 200미터보다 아래에 있어요.",
 "동해 단면도, 남산 실루엣 13개가 쌓여도 바닥에 못 닿는 애니메이션", "평균 1,684미터, 최대 3,762미터, 89퍼센트가 200미터 아래",
 "Cross-section diagram of the East Sea showing dramatic depth, a column of thirteen tiny stacked mountain silhouettes with a tower on top not reaching the seabed, deep blue gradient darkening downward", "I"),
("왜 이렇게 됐을까요. 동해는 바깥 바다로 나가는 출구가 네 개밖에 없어요. 대한해협, 쓰가루, 소야, 타타르. 그런데 이 출구가 전부 폭이 좁고 수심이 200미터도 안 돼요. 그러니까 200미터 아래 깊은 물은 밖으로 못 나가요. 거대한 그릇에 갇혀 있는 거예요.",
 "동해 지도에 네 개 해협이 표시되고, 그릇 모양 단면 그래픽으로 심층수가 갇힌 모습", "출구 4개, 모두 수심 200미터 미만",
 "Stylized bowl-shaped cross-section of the East Sea basin, four narrow shallow openings at the rim, deep dark water trapped inside", "I"),
("그래서 해양학자들은 동해를 미니 대양이라고 불러요. 태평양 같은 큰 바다에서 일어나는 심층수 순환이 동해 안에서도 똑같이 일어나거든요. 표층의 물이 겨울에 차가워져서 가라앉고, 바닥을 돌아서 다시 올라오는 순환이요.",
 "동해 수중, 표층에서 심층으로 내려가는 물 흐름 화살표 애니메이션", "미니 대양",
 "Underwater view descending from sunlit surface into pitch black abyss of the East Sea, shafts of light fading, particles drifting, vast and silent", "P"),
("다른 대양은 이 순환이 천 년에서 이천 년 걸리는데, 동해는 백 년이면 한 바퀴 돌아요. 게다가 남쪽은 아열대, 북쪽은 아한대예요. 지구 바다에서 일어나는 일을 스무 배 빠른 속도로 보여주는 축소판이 우리 집 앞에 있는 거예요. 그래서 전 세계 해양학자들이 기후변화 연구하려고 동해로 옵니다.",
 "해양조사선 갑판, 연구원이 관측장비 내리는 장면", "대양 1,000~2,000년 / 동해 100년",
 "Ocean research vessel on the open East Sea at dawn, scientists on deck lowering a cylindrical CTD instrument into dark water, cold steel gray sky", "P"),
]))

S.append(("서해, 9미터 조차와 세계 최대 조력발전", [
("서해는 정반대예요. 평균 수심이 40미터 정도. 얕아요. 동해 평균 수심의 40분의 1이에요. 대신 물이 하루에 두 번 엄청나게 들고 나가요.",
 "동해와 서해 수심 비교 막대, 이어서 서해 갯벌 조수 타임랩스", "평균 수심 약 40미터, 하루 두 번",
 "Time-lapse style wide shot of the West Sea coast, tide receding to reveal vast mud flats then rushing back, dramatic sky, long shadows", "P"),
("인천 앞바다 조차가 최대 9미터가 넘어요. 3층 건물 높이만큼 바다가 오르락내리락하는 거예요. 추석 무렵 슈퍼문이 뜨면 10미터까지 벌어져요. 세계적으로 조차가 큰 바다로 꼽혀요.",
 "부두 기둥에 물 높이 표시, 같은 기둥의 만조와 간조 비교, 3층 건물 실루엣 겹치기", "인천 조차 최대 9미터, 슈퍼문 10미터",
 "Same harbor pier pillar shown at high tide with water near the top and at low tide fully exposed with barnacles, side by side, overcast coastal light", "P"),
("이 힘으로 뭘 하냐면, 시화호에 세계 최대 조력발전소를 돌려요. 254메가와트, 1년에 552기가와트시. 인구 50만 도시 하나가 쓰는 전기예요. 바닷물이 밀려오고 빠져나가는 것만으로요.",
 "시화호 조력발전소 항공 뷰, 수문 클로즈업에서 도시 야경으로 디졸브", "시화호 조력발전소, 세계 최대, 254메가와트, 인구 50만 도시",
 "Aerial view of Sihwa Lake tidal power station, long straight seawall with ten turbine gates, seawater rushing through in white foam, golden hour", "P"),
("원래 시화호는 1990년대에 방조제로 막았다가 물이 썩어서 시궁창 냄새가 난다고 전국 뉴스에 나오던 곳이에요. 그걸 수문을 열고 발전소를 얹어서 1년에 바닷물 1억 4,500만 톤을 안팎으로 갈아 넣는 정화 장치로 바꿨어요. 이 얘기도 나중에 다시 나옵니다.",
 "1990년대 뉴스 화면 느낌의 오염된 호수, 이어서 현재 맑아진 시화호", "1990년대 오염 → 연 1억 4,500만 톤 해수 순환",
 "Murky greenish polluted lake surface with foam and dead fish near a concrete embankment, 1990s news footage look, grainy", "P"),
]))

S.append(("남해, 두 해류가 만드는 세계 최고 밀도", [
("남해는 또 달라요. 남쪽에서 따뜻한 대마난류가 올라오고, 북쪽에서 차가운 북한한류가 내려와서 여기서 만나요. 계절마다 어느 쪽이 세냐에 따라 바다 성격이 바뀌어요.",
 "지도 위 주황 난류와 파랑 한류 화살표가 남해에서 충돌", "대마난류, 북한한류",
 "Ocean current map illustration, a warm orange current sweeping up from the south and a cold blue current flowing down from the north colliding and swirling around the southern coast of Korea", "I"),
("찬물을 따라 내려온 물고기랑 따뜻한 물을 타고 올라온 물고기가 한 바다에 섞이는 거예요. 한 바다에서 두 기후대의 생물을 동시에 보는 거죠.",
 "수중 촬영, 다양한 어종 몽타주 3연속 빠른 컷", "자막 없음",
 "Underwater scene in the South Sea of Korea, a school of silver fish passing rocky reef covered in colorful soft corals and kelp, sunlight rays from above, vibrant marine life", "P"),
("그래서 이런 결과가 나옵니다. 2000년부터 2010년까지 전 세계 과학자 2,700명이 10년 동안 바다 생물을 센 해양생물센서스라는 게 있어요. 인류 역사상 가장 큰 해양 생물 조사예요.",
 "세계지도 위에 조사 해역 25곳이 점으로 켜짐", "해양생물센서스 2000~2010, 과학자 2,700명",
 "World map with twenty five glowing dots marking ocean survey regions, thin connecting lines, scientific data visualization feel", "I"),
("조사한 25개 해역 중에서 면적에 비해 사는 생물 종이 가장 많은 바다가 어디였을까요. 한국이었어요. 좁은 바다에 이렇게 많은 종이 사는 곳이 없었다는 거예요. 중국, 남아프리카, 발트해, 멕시코만이 그 뒤였어요.",
 "한국 해역만 금색으로 켜지고 뒤이어 2~5위 지역이 은색으로", "면적 대비 생물 종 수 세계 최고",
 "The same world map now dimmed except the seas around the Korean Peninsula glowing bright gold, radiating light", "I"),
]))

S.append(("대국 비교", [
("정리해 볼게요. 깊은 바다, 얕은 바다, 두 해류가 만나는 바다. 이 세 개가 자동차로 반나절 거리 안에 다 있어요.",
 "한반도 지도 위에 세 바다 아이콘과 자동차 이동 경로", "반나절 거리",
 "Map of South Korea with three sea icons on each coast connected by a short glowing road line, compact and dense", "I"),
("미국은 태평양과 대서양이 있지만 차로 닷새를 달려야 반대편 바다를 봐요. 러시아는 해안선은 길지만 대부분 일 년의 절반이 얼어 있어요. 중국은 바다가 동쪽 한 면에만 있어요.",
 "미국 횡단 경로 애니메이션, 러시아 결빙 해안 실사, 중국 동쪽 해안만 하이라이트 3연속", "닷새 / 결빙 / 한 면",
 "Aerial view of a frozen Arctic coastline, cracked white sea ice meeting gray tundra, icy blue tones, vast and desolate", "P"),
("우리는 아침에 동해에서 해 보고 저녁에 서해에서 해 지는 걸 봐요. 강릉에서 인천까지 세 시간이에요. 이게 그 미국 친구가 말한 거였어요. 없는 게 아니라, 다 모여 있는 거.",
 "좌우 분할, 왼쪽 동해 일출, 오른쪽 서해 일몰", "아침 동해, 저녁 서해",
 "Diptych, left panel a fiery sunrise over the calm East Sea horizon with rocky shore, right panel a soft orange sunset over West Sea mud flats, matching horizon lines", "P"),
]))

S.append(("갯벌, 세계 5대", [
("그리고 이제, 오늘 영상의 주인공이에요. 서해 갯벌.",
 "화면 암전 후 갯벌 광각 드론 등장, 음악 전환", "서해 갯벌",
 "Vast Korean tidal flat at low tide stretching to the horizon, intricate branching mud channel patterns reflecting a pale sky, wide aerial drone shot", "P"),
("갯벌이 생기려면 조건이 세 개 맞아야 해요. 바다가 얕아야 하고, 조차가 커야 하고, 강이 진흙을 계속 실어 와야 해요. 서해는 이 셋이 다 있어요. 얕고, 9미터 조차에, 한강 금강 영산강이 진흙을 쏟아부어요.",
 "세 조건 아이콘이 하나씩 체크되고, 지도에 한강 금강 영산강 하구가 표시됨", "얕은 수심 + 큰 조차 + 강의 퇴적물",
 "Aerial view of a wide muddy river mouth fanning out into the sea, brown sediment plumes swirling into pale green water, delta patterns", "P"),
("그래서 세계에서 갯벌이 큰 곳 다섯 군데 중 하나가 됐어요. 유럽 북해 연안, 미국 동부, 캐나다 동부, 아마존 강 하구, 그리고 한국 서남해안.",
 "세계지도에 5곳 순차 표시, 한국이 마지막에 켜짐", "북해, 미국 동부, 캐나다 동부, 아마존 하구, 한국",
 "World map with five coastal regions highlighted in amber, Europe North Sea, US east coast, Canada east coast, Amazon estuary, and Korea west coast", "I"),
("다른 네 곳은 대륙 규모 해안선이 만든 거예요. 우리는 10만 제곱킬로미터 안에 2,482제곱킬로미터를 갖고 있어요. 국토의 2.5퍼센트가 갯벌인 나라입니다. 서울 면적의 네 배가 하루 두 번 물에 잠기고 다시 드러나요.",
 "한반도 지도에서 서남해안 갯벌 영역만 갈색으로 채워지고 서울 면적 네 개와 비교", "2,482제곱킬로미터, 국토의 2.5퍼센트, 서울의 4배",
 "Map of South Korea with the entire western and southern coastline fringed in rich brown tidal flat areas, glowing softly", "I"),
]))

S.append(("갯벌이 하는 일", [
("이 갯벌이 하는 일을 볼게요. 서울대 김종성 교수팀이 2017년부터 4년 동안 전국 갯벌 스무 곳의 흙을 파서 분석했어요. 진흙 속에 탄소가 얼마나 쌓여 있는지, 매년 얼마나 새로 쌓이는지요.",
 "연구원들이 장화 신고 갯벌에서 코어 채취하는 장면", "2017~2020, 전국 갯벌 20곳",
 "Marine researchers in rubber boots and waders kneeling on a tidal flat, pushing a clear sediment core tube into dark mud, overcast sky, field science documentary", "P"),
("그 결과 우리 갯벌에 탄소 1,300만 톤이 묻혀 있고, 매년 26만 톤의 이산화탄소를 새로 빨아들이고 있다는 걸 세계 최초로 밝혔어요. 국가 단위로 갯벌 탄소를 계산한 게 우리가 처음이에요.",
 "갯벌 단면 그래픽, 진흙층 속으로 탄소 입자가 가라앉아 쌓이는 애니메이션", "탄소 1,300만 톤 저장, 연 26만 톤 흡수",
 "Scientific cross-section illustration of tidal flat sediment layers, dark carbon particles sinking from the water and accumulating in deep mud strata", "I"),
("26만 톤이 어느 정도냐면, 승용차 11만 대가 1년 내내 뿜는 양이에요. 그걸 그냥 진흙이 먹는 거예요. 인터넷에 20만 대라고 쓴 글도 있는데, 연구 원문은 11만 대예요.",
 "위에서 본 거대한 주차장 가득한 자동차, 이어서 갯벌로 디졸브. 20만에 취소선, 11만 강조", "승용차 11만 대분",
 "Aerial top-down view of an enormous parking lot packed with tens of thousands of cars in neat rows extending beyond the frame, hazy afternoon light", "P"),
("게다가 숲이랑 달라요. 숲은 나무가 죽거나 산불이 나면 탄소를 다시 내놓아요. 갯벌은 진흙 속에 수천 년 가둬 둡니다. 그래서 요즘 이걸 블루카본이라고 부르고 전 세계가 주목하고 있어요.",
 "산불 장면과 고요한 갯벌 대비 2분할, 블루카본 텍스트", "블루카본",
 "Split image, left a forest fire releasing smoke into the sky, right a calm dark tidal flat under blue dusk light, stark contrast", "P"),
("생물은요. 이 갯벌에 2,446종이 살아요. 새만 216종이고 그중 24종이 국제 멸종위기종이에요. 게, 낙지, 짱뚱어, 갯지렁이 같은 바닥 생물만 1,349종이에요.",
 "갯벌 생물 몽타주, 칠게, 짱뚱어, 낙지 매크로 빠른 컷", "2,446종, 조류 216종, 저서동물 1,349종",
 "Macro shot of a small fiddler crab with one oversized claw on wet Korean mud flat, tiny air holes around it, shallow focus, soft daylight", "P"),
("특히 새요. 서천 앞바다에 유부도라는 작은 섬이 있어요. 동아시아에서 호주까지 오가는 도요물떼새가 63종인데, 그중 24종이 이 섬 하나에 내려앉아요. 멸종위기종만 17종이에요.",
 "유부도 위치 지도 줌인, 이어서 도요새 무리 실사", "유부도, 63종 중 24종, 멸종위기 17종",
 "Small flat island surrounded by vast exposed tidal flats at low tide, seen from a high drone angle, thin channels of water glinting", "P"),
("시베리아나 알래스카에서 번식하고 호주나 뉴질랜드에서 겨울을 나는 새들이에요. 그 사이 수천 킬로미터를 날아오다가 딱 한 번 내려서 먹고 쉬는 데가 우리 서해 갯벌이에요. 우리 갯벌이 없어지면 그 새들은 태평양 위에서 떨어져요.",
 "동아시아 대양주 이동 경로 지도, 시베리아에서 한국을 거쳐 호주로 이어지는 선, 이어서 도요새 수천 마리 이륙", "시베리아 → 서해 갯벌 → 호주",
 "Thousands of migratory shorebirds lifting off together from a Korean tidal flat at dawn, dense swirling flock against a pale pink and gold sky, wildlife documentary photography", "P"),
("돈으로 따지면요. 정부가 2003년에 계산한 게 1제곱킬로미터당 연 39억 원이에요. 전체로 하면 1년에 10조 원. 수산물, 정화, 재해 방지, 관광을 다 합친 값이에요. 그냥 거기 있기만 해도요.",
 "10조 원 카운터, 수산물 정화 방재 관광 네 아이콘", "연 10조 원",
 "Fisherwomen in wide hats harvesting clams and octopus on a glistening Korean mud flat, baskets and small sleds, late afternoon light", "P"),
]))

S.append(("유네스코, 두 번의 인정", [
("그래서 2021년 7월에 유네스코가 한국의 갯벌을 세계자연유산으로 올렸어요. 서천, 고창, 신안, 보성-순천 네 곳이었어요. 제주 화산섬 이후 14년 만에 나온 우리나라 두 번째 자연유산이에요.",
 "서남해안 지도에 4곳이 금색으로 켜짐", "2021년 7월 26일, 세계자연유산",
 "Map of the southwestern coast of Korea with four tidal flat regions lighting up in gold one after another, elegant heritage emblem style", "I"),
("그런데 그때 유네스코가 조건을 하나 달았어요. 이거 좋은데, 범위가 너무 좁다. 더 넓혀서 다시 오라고. 그래서 5년을 준비했어요.",
 "유네스코 결정문 문서 느낌 그래픽, '확대 등재 권고' 부분 하이라이트", "범위를 넓혀서 다시 오라",
 "Close-up of an official document page with a highlighted paragraph, formal serif typography blurred, a fountain pen resting beside", "P"),
("그리고 올해, 2026년 7월 25일에 부산에서 열린 제48차 세계유산위원회에서 범위를 넓히는 게 확정됐습니다. 여수, 고흥, 무안, 서산 갯벌이 추가돼서 6개 구성요소, 유산구역 15만 6천 헥타르가 됐어요.",
 "국제회의장, 의사봉 내리는 순간. 이어서 지도에서 4곳이 6개 구성요소로 확장", "2026년 7월 25일 부산, 6개 구성요소, 15만 6,386헥타르",
 "Large international conference hall with rows of delegates at curved desks, country name plates, a giant screen at the front, a gavel coming down at the podium, formal lighting", "P"),
("우리나라에서 열린 회의에서 우리 갯벌이 넓어진 거예요. 그 회의장에 앉아 있던 각국 대표들이 손을 들어서요.",
 "회의장 박수, 한국 대표단 미소, 지도 최종 확장 상태", "부산에서, 우리 손으로",
 "The same southwestern Korea map, golden heritage zones expanding outward and merging into six larger glowing regions", "I"),
]))

S.append(("반전 하나, 편애받은 땅이 아니었다", [
("여기까지 들으면 진짜 신이 편애한 것 같죠. 심은 숲, 깨끗한 물, 조용한 자리, 세 가지 바다, 세계 최고 갯벌. 그런데 이제 그 반전이에요.",
 "앞서 나온 숲, 약수, 바다, 갯벌 4컷이 빠르게 재생된 뒤 화면이 급격히 차가운 톤으로", "그런데",
 "Four-panel grid of Korean landscapes, forest, spring water, deep sea, tidal flat, colors draining to cold desaturated blue-gray, cinematic mood shift", "P"),
("이 땅은 편애받은 땅이 아니에요. 아까 산림 얘기할 때 기억해 두라고 했잖아요. 우리 숲은 신이 준 게 아니라 우리 부모님 세대가 65억 그루를 손으로 심어서 만든 거예요. 원래 있던 걸 지킨 게 아니라, 다 잃은 다음에 다시 만든 거예요.",
 "한 노인의 손에 든 묘목 클로즈업, 이어서 그 손이 심은 자리에 자란 큰 나무", "65억 그루, 손으로 심은 숲",
 "Close-up of weathered elderly Korean hands gently holding a small pine seedling with soil on the roots, soft overcast light, shallow depth of field", "P"),
("그리고 갯벌은요. 이게 더 아픈 얘기예요. 1987년부터 1997년까지 딱 10년 동안 간척 사업으로 갯벌 810제곱킬로미터가 사라졌어요. 지금 남은 갯벌의 3분의 1이 10년 만에 없어진 거예요.",
 "서해안 지도에서 사라진 갯벌 영역이 붉게 표시", "1987~1997, 810제곱킬로미터 소멸",
 "Map of Korea's west coast with large red hatched zones marking vanished tidal flats and only a thin brown fringe remaining, stark contrast", "I"),
("새만금이에요. 1991년에 첫 삽을 떠서 2010년에 끝났어요. 19년, 2조 9천억 원. 길이 33.9킬로미터. 네덜란드 방조제를 제치고 세계에서 가장 긴 방조제로 기네스북에 올랐어요.",
 "새만금 방조제 항공 뷰, 직선 콘크리트가 수평선까지 이어짐. 33.9킬로미터 자막", "1991~2010, 19년, 2조 9천억 원, 33.9킬로미터 세계 최장",
 "Aerial view of the Saemangeum seawall, a perfectly straight concrete line dividing brown dry reclaimed land from the open gray sea, stretching to the horizon, overcast sky", "P"),
("그 안에 있던 연안습지가 401제곱킬로미터예요. 지금 유네스코에 올라간 갯벌 유산구역의 4분의 1이 넘는 크기가 한 사업으로 없어진 거예요.",
 "새만금 매립지 내부, 마른 진흙 바닥과 죽은 조개껍데기", "연안습지 401제곱킬로미터",
 "Cracked dry mud of a former tidal flat behind a seawall, scattered bleached clam shells, no water in sight, harsh flat light, somber", "P"),
("시화호도 같은 시기예요. 아까 조력발전소 얘기했잖아요. 그거 원래 갯벌 막아서 만든 호수예요. 물이 썩어서 결국 바닷물을 다시 들여야 했고, 그 과정에서 발전소가 나온 거예요. 성공 사례처럼 보이지만 출발은 실패였어요.",
 "시화호 오염 시절 사진에서 현재 발전소로 디졸브, 아래에 타임라인", "시화호, 실패에서 나온 성공",
 "Wide aerial view of Sihwa Lake seawall at dusk, tidal gates open with water flowing through, half the frame lake and half sea, contemplative mood", "P"),
("네이처에 실린 연구를 보면 황해 갯벌은 지난 30년간 28퍼센트가 줄었어요. 전 세계 갯벌이 16퍼센트 줄었는데 우리 바다는 거의 두 배 속도로 사라진 거예요. 우리가 지금 자랑하는 유네스코 갯벌은 그 나머지예요.",
 "막대그래프 세계 16퍼센트 대 황해 28퍼센트, 위성 사진 1984 대 2016 비교", "세계 16퍼센트 감소 / 황해 28퍼센트 감소",
 "Two satellite images of the same Yellow Sea coastline side by side, 1980s with wide brown tidal flats and 2010s with straight seawalls and reclaimed land", "I"),
("간척은 원래 오래된 일이에요. 고려사에 1256년 강화도에서 둑을 쌓아 땅을 만들었다는 기록이 있어요. 800년 전부터 했어요. 다만 그때는 삽으로 했고, 1990년대엔 중장비로 했다는 게 다른 거예요.",
 "고려사 고문서 느낌 이미지, 이어서 대형 덤프트럭과 준설선", "1256년 강화도, 800년의 간척",
 "Ancient Korean manuscript page with vertical brush calligraphy on aged hanji paper, soft candlelight, shallow focus", "P"),
]))

S.append(("반전 둘, 아직 조용한 땅", [
("물도 그래요. 비는 세계 평균의 1.6배 오는데, 사람이 많아서 1인당으로 나누면 세계 평균의 17퍼센트밖에 안 돼요. 그리고 그 비의 절반 이상이 여름 두 달에 몰려서 와요. 겨울엔 연간 강수량의 10분의 1도 안 돼요. 유엔 기준으로 우리는 물 스트레스 국가예요.",
 "말라붙은 저수지 바닥, 이어서 월별 강수량 그래프가 여름에만 치솟는 애니메이션", "1인당 강수량 세계 평균 17퍼센트, 물 스트레스 국가",
 "Cracked dry reservoir bed with a stranded small boat, receding water line visible on the far bank, harsh midday sun", "P"),
("지진도요. 아까 판 안쪽이라 조용하다고 했죠. 그런데 지난 8월에 학자들이 이렇게 경고했어요. 판 안쪽이라는 게 바로 긴장해야 할 이유라고. 서쪽에서 인도판이 밀고, 동쪽에서 태평양판이 밀고, 그 힘이 한반도 안에 있는 오래된 단층에 조금씩 쌓이고 있대요. 경주, 포항 지진이 그 신호였어요.",
 "판 경계 지도에 양쪽에서 화살표가 한반도를 압박, 지진계 그래프, 포항 지진 피해 건물", "판 내부 응력 축적, 경주 2016, 포항 2017",
 "Tectonic map of East Asia with large arrows pressing inward on the Korean Peninsula from the Indian plate in the west and the Pacific plate in the east, faults glowing faintly orange", "I"),
("그러니까 이 땅은 조용한 땅이 아니라, 아직 조용한 땅이에요.",
 "검은 화면에 문장 하나만", "조용한 땅이 아니라, 아직 조용한 땅",
 "Pure black background with a single thin white horizontal line of light in the center, minimalist, cinematic void, subtle film grain", "P"),
]))

S.append(("클로징", [
("그러니까 이 땅의 진짜 가치는 이거예요. 신이 준 게 아니라, 망가졌던 걸 다시 살려낸 기록이 있는 땅이라는 거.",
 "다시 따뜻한 톤, 숲이 갯벌 해안선과 만나는 골든아워 드론", "신이 준 게 아니라 살려낸 땅",
 "Golden hour aerial shot where dense green Korean forest slopes meet a shimmering tidal flat coastline, warm hopeful light, cinematic wide shot", "P"),
("숲을 없던 데서 만들어 봤고, 썩은 호수를 발전소로 바꿔 봤고, 갯벌도 반이 사라진 뒤에 남은 걸 세계유산으로 지켜냈어요. 그 세 가지를 다 해본 나라, 저는 다른 나라를 못 찾았어요.",
 "숲, 시화호 발전소, 유네스코 갯벌 3컷이 차례로 따뜻한 톤으로 다시 등장", "숲 / 시화호 / 갯벌",
 "Triptych of Korean landscapes in warm light, a dense pine forest, a tidal power seawall at sunset, and a golden tidal flat with birds, unified color grade", "P"),
("그 미국 친구한테 이제 대답할 수 있을 것 같아요. 작은데 많이 들어 있는 게 아니라, 작으니까 하나도 버리지 않고 다 살려 쓴 거라고요. 그리고 아직 다 살린 건 아니라고요.",
 "카페 지도 장면으로 복귀, 이번엔 한국인 손이 지도 위 서해안을 가리킴", "하나도 버리지 않고 다 살려 쓴 땅",
 "Same wooden cafe table with the paper map of South Korea, now a Korean hand pointing at the west coast, two coffee cups, warm late afternoon window light, shallow depth of field", "P"),
("여러분은 우리 땅에서 가장 아까운 게 뭐라고 생각하세요. 댓글로 남겨 주시면 다음 영상에서 그 주제로 찾아보겠습니다. 다음 영상에서는 이 갯벌 810제곱킬로미터가 사라지던 10년 동안 무슨 일이 있었는지, 새만금의 진짜 이야기를 다뤄 볼게요. 구독하시면 놓치지 않고 보실 수 있어요. 오늘도 봐 주셔서 감사합니다.",
 "엔드 스크린, 왼쪽 구독 버튼 모션, 오른쪽 다음 영상 새만금 예고 카드", "댓글로 알려주세요, 다음 영상 새만금의 진짜 이야기",
 "Aerial view of the Saemangeum seawall at dusk with dramatic clouds, moody teaser atmosphere, space left on both sides for overlay elements, cinematic wide shot", "P"),
]))

def syl(t):
    return sum(1 for c in t if '가'<=c<='힣') + 1.5*sum(1 for c in t if c.isdigit())
def ts(sec):
    sec=int(round(sec)); return f"{sec//60}:{sec%60:02d}"

# 시간 계산
t=0.0; cuts=[]; scene_ranges=[]
for si,(title,cs) in enumerate(S,1):
    s0=t
    for c in cs:
        d=syl(c[0])/SPM*60 + 1.0   # 컷 전환 여유 1초
        cuts.append((si,title,c,t,t+d)); t+=d
    scene_ranges.append((si,title,s0,t))
total=t
total_syl=sum(syl(c[0]) for _,cs in S for c in cs)

script="\n\n".join(" ".join(c[0] for c in cs) for _,cs in S)

sb=[]
sb.append(f"6단계. 스토리보드 ({len(S)}장면, {len(cuts)}컷, 총 {ts(total)})\n")
sb.append("형식: 컷 번호 / 대본 구간 / 화면 구성 / 자막 포인트 / 예상 시간 / Image Prompt")
sb.append("컷 시간은 대본 음절 수를 분당 290음절로 환산하고 컷마다 전환 여유 1초를 더해 계산했다. 나레이션 속도가 다르면 전체가 비례해서 늘거나 줄어든다.")
sb.append(f"이미지 생성 시 실사 컷(P)은 프롬프트 뒤에 다음 문구를 붙인다: {STYLE_PHOTO}")
sb.append(f"지도와 인포그래픽 컷(I)은 다음 문구를 붙인다: {STYLE_INFO}\n")
n=0
for si,title,s0,s1 in scene_ranges:
    sb.append(f"\n장면 {si}. {title} ({ts(s0)}~{ts(s1)})\n")
    for (csi,_,c,a,b) in cuts:
        if csi!=si: continue
        n+=1
        line, vis, sub, ip, st = c
        sb.append(f"컷 {n} ({st}) / {line} / {vis} / 자막: {sub} / {ts(a)}~{ts(b)} / Image Prompt: {ip}\n")
storyboard="\n".join(sb)

# 타임라인(설명란용)
timeline="\n".join(f"{ts(s0).rjust(5,'0') if False else ts(s0)} {title}" for _,title,s0,_ in scene_ranges)

open('/tmp/claude-0/-home-user-autoworkers/1decb9f8-37f5-533a-85e6-6b640cad5259/scratchpad/out_script.txt','w',encoding='utf-8').write(script)
open('/tmp/claude-0/-home-user-autoworkers/1decb9f8-37f5-533a-85e6-6b640cad5259/scratchpad/out_storyboard.txt','w',encoding='utf-8').write(storyboard)
open('/tmp/claude-0/-home-user-autoworkers/1decb9f8-37f5-533a-85e6-6b640cad5259/scratchpad/out_timeline.txt','w',encoding='utf-8').write(timeline)
print("총 음절", int(total_syl), "컷", len(cuts), "장면", len(S))
for spm in (260,290,320): print(spm, "음절/분 ->", round(total_syl/spm + len(cuts)/60,1), "분")
print(timeline)
