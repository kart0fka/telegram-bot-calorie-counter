from datetime import datetime

from aiogram import Dispatcher, filters, types
from aiogram.dispatcher import FSMContext

from config import TELEGRAM_BOT_SUPERUSER_ID
from db import Database
from db.structures import create_user, create_record
from keyboards import (
    GENDER_INLINE_KEYBOARD,
    MENU_INLINE_KEYBOARD,
    CALCULATE_FINISH_INLINE_KEYBOARD,
    LANGUAGE_INLINE_KEYBOARD,
    UNIT_INLINE_KEYBOARD,
    TIME_ZONE_INLINE_KEYBOARD,
    SETTINGS_END_INLINE_KEYBOARD,
    get_keyboard_of_nums,
)
from utils.utils import kcal_limit, limits
from utils.states import CalculateState, RecordState, SettingsState

db_users = Database('users')


# COMMANDS
async def command_start(message: types.Message) -> None:
    await message.answer(
        ('Hello!\n' 'Select is your language'),
        reply_markup=LANGUAGE_INLINE_KEYBOARD,
    )
    await SettingsState.language.set()
    user_id = message.from_user.id
    db_users.add_records(
        create_user(
            user_id=user_id,
            is_admin=user_id == TELEGRAM_BOT_SUPERUSER_ID,
            is_superuser=user_id == TELEGRAM_BOT_SUPERUSER_ID,
        )
    )


async def command_menu(message: types.Message) -> None:
    await message.answer('Menu', reply_markup=MENU_INLINE_KEYBOARD)


async def command_profile(message: types.Message) -> None:
    user_id = message.from_user.id
    user = db_users.get_records({'user_id': user_id}, 1)
    calorie_limit = user['limits']['calories']
    protein_limit = user['limits']['protein']
    fat_limit = user['limits']['fat']
    carb_limit = user['limits']['carb']

    await message.answer(
        (
            'Your profile\n'
            f'Protein: 0/{protein_limit} g\n'
            f'Fat: 0/{fat_limit} g\n'
            f'Carb: 0/{carb_limit} g\n'
            f'Calories: 0/{calorie_limit} kcal\n'
        )
    )


# CALLBACKS
async def callback_calculate_calories(
    callback_query: types.CallbackQuery,
) -> None:
    await callback_query.message.edit_reply_markup(None)
    await command_calculate_calories(callback_query.message)


async def callback_open_menu(callback_query: types.CallbackQuery) -> None:
    await callback_query.message.edit_reply_markup(None)
    await command_menu(callback_query.message)


async def callback_profile(callback_query: types.CallbackQuery) -> None:
    await callback_query.message.edit_reply_markup(None)
    callback_query.message.from_user = callback_query.from_user
    await command_profile(callback_query.message)


# STATES
# Settings state
async def settings_state_language(
    callback_query: types.CallbackQuery, state: FSMContext
) -> None:
    await callback_query.message.edit_reply_markup(None)
    lang = callback_query.data[len('language_'):]  # fmt: skip
    await state.update_data({'language': lang})
    await SettingsState.next()

    await callback_query.message.answer(
        'Select your mass unit', reply_markup=UNIT_INLINE_KEYBOARD
    )


async def settings_state_unit(
    callback_query: types.CallbackQuery, state: FSMContext
) -> None:
    await callback_query.message.edit_reply_markup(None)
    answer = callback_query.data[len('unit_'):]  # fmt: skip
    await state.update_data({'mass': answer})
    await SettingsState.next()

    await callback_query.message.answer(
        'Select your time zome', reply_markup=TIME_ZONE_INLINE_KEYBOARD
    )


async def settings_state_time_zone(
    callback_query: types.CallbackQuery, state: FSMContext
) -> None:
    await callback_query.message.edit_reply_markup(None)
    answer = callback_query.data[len('zone_'):]  # fmt: skip
    await state.update_data({'utc': answer})

    data = await state.get_data()
    db_users.update_elem(
        {'user_id': callback_query.from_user.id}, {'settings': data}
    )
    await state.finish()

    await callback_query.message.answer(
        'Your choices saved\nCalculate your limits?',
        reply_markup=SETTINGS_END_INLINE_KEYBOARD,
    )


# Calculate State
async def command_calculate_calories(message: types.Message) -> None:
    await CalculateState.for_what.set()
    await message.answer(
        (
            'Choose what do you want:\n\n'
            '1. Weight gain\n'
            '2. Control of the diet\n'
            '3. For the weigth loss\n'
        ),
        reply_markup=get_keyboard_of_nums(3, prefix='for_what'),
    )


async def calculate_state_for_what(
    callback_query: types.CallbackQuery, state: FSMContext
) -> None:
    ind = int(callback_query.data[len('for_what_'):])  # fmt: skip
    await callback_query.message.edit_reply_markup(None)
    await state.update_data({'for_what': ind})
    await CalculateState.next()

    await callback_query.message.answer(
        'Choose your gender', reply_markup=GENDER_INLINE_KEYBOARD
    )


async def calculate_state_gender(
    callback_query: types.CallbackQuery, state: FSMContext
) -> None:
    answer = int(callback_query.data[len('gender_'):])  # fmt: skip
    await callback_query.message.edit_reply_markup(None)
    await state.update_data({'gender': answer})
    await CalculateState.next()

    await callback_query.message.answer('Input your age')


async def calculate_state_age(
    message: types.Message, state: FSMContext
) -> None:
    if not message.text.isdigit():
        await message.answer("It must be a number")
        return
    await state.update_data({'age': int(message.text)})
    await CalculateState.next()

    await message.answer('Input your growth(rounded)')


async def calculate_state_growth(
    message: types.Message, state: FSMContext
) -> None:
    if not message.text.isdigit():
        await message.answer("It must be a number")
        return
    await state.update_data({'growth': int(message.text)})
    await CalculateState.next()

    await message.answer('Input your weight(rounded)')


async def calculate_state_weight(
    message: types.Message, state: FSMContext
) -> None:
    if not message.text.isdigit():
        await message.answer("It must be a number")
        return
    await state.update_data({'weight': int(message.text)})
    await CalculateState.next()

    await message.answer(
        (
            'Choose your activity coefficient:\n\n'
            '1. Minimum physical activity\n'
            '2. Workout 3 times per week\n'
            '3. Workout 5 times per week\n'
            '4. Intensive workout 5 times per week\n'
            '5. Workout every day\n'
            '6. Intensive workout every day or 2 times per day\n'
            '7. Physical activity every day + physical work\n'
        ),
        reply_markup=get_keyboard_of_nums(7, prefix='activity'),
    )


async def calculate_state_activity(
    callback_query: types.CallbackQuery, state: FSMContext
) -> None:
    await callback_query.message.edit_reply_markup(None)
    activity = int(callback_query.data[len('activity_'):])  # fmt: skip
    data = await state.get_data()
    result = kcal_limit(
        data['weight'], data['growth'], data['age'], data['gender'], activity
    )
    result_limits = limits(result, data['for_what'])
    await state.set_data({'result': result, 'limits': result_limits})

    await callback_query.message.answer(
        (
            f'Your calorie limit: {result} kcal\n'
            f'Your protein limit: {result_limits[0]} g\n'
            f'Your fat limit: {result_limits[1]} g\n'
            f'Your carb limit: {result_limits[2]} g\n'
            'Write this number to your calorie limit?'
        ),
        reply_markup=CALCULATE_FINISH_INLINE_KEYBOARD,
    )
    await CalculateState.next()


async def calculate_state_waiting_for_finish(
    callback_query: types.CallbackQuery, state: FSMContext
) -> None:
    ind = int(callback_query.data[len('calculate_finish_'):])  # fmt: skip
    if ind == 2:
        # TODO: write a change limits after calculate
        return
    await callback_query.message.edit_reply_markup(None)
    answer = bool(ind)
    if answer:
        data = await state.get_data()
        db_users.update_elem(
            {'user_id': callback_query.from_user.id},
            {
                'limits': {
                    'calories': data['result'],
                    'protein': data['limits'][0],
                    'fat': data['limits'][1],
                    'carb': data['limits'][2],
                }
            },
        )
        await callback_query.message.answer('Limit saved')
    await command_menu(callback_query.message)
    await state.finish()


async def calculate_state_cancel(
    message: types.Message, state: FSMContext
) -> None:
    await state.finish()
    await message.answer('Cancel state')
    await command_menu(message)


# Record state
async def command_record(message: types.Message) -> None:
    await RecordState.weight.set()
    await message.answer('Input the weight of eaten')


async def callback_record(callback_query: types.CallbackQuery) -> None:
    await callback_query.message.edit_reply_markup(None)
    await command_record(callback_query.message)


async def record_state_weight(
    message: types.Message, state: FSMContext
) -> None:
    if not message.text.isdigit():
        message.answer('It must be a number(gram)')
        return
    answer = int(message.text)
    await state.update_data({'mass': answer / 100})
    await RecordState.next()

    await message.answer('Input the weight of protein per 100 grams')


async def record_state_protein(
    message: types.Message, state: FSMContext
) -> None:
    if not message.text.isdigit():
        message.answer('It must be a number(gram)')
        return
    answer = int(message.text)
    mass = (await state.get_data())['mass']
    await state.update_data({'protein': answer * mass})
    await RecordState.next()

    await message.answer('Input the weight of fat per 100 grams')


async def record_state_fat(message: types.Message, state: FSMContext) -> None:
    if not message.text.isdigit():
        message.answer('It must be a number(gram)')
        return
    answer = int(message.text)
    mass = (await state.get_data())['mass']
    await state.update_data({'fat': answer / mass})
    await RecordState.next()

    await message.answer('Input the weight of fat per 100 grams')


async def record_state_carb(message: types.Message, state: FSMContext) -> None:
    if not message.text.isdigit():
        message.answer('It must be a number(gram)')
        return
    answer = int(message.text)
    mass = (await state.get_data())['mass']
    await state.update_data(
        {'carb': answer / mass, 'time': datetime.utcnow().isoformat()}
    )

    data = await state.get_data()
    data.pop('mass')
    db_users.update_elem(
        {'user_id': message.from_user.id},
        {'records': create_record(**data)},
        'push',
    )
    await state.finish()

    await message.answer('Recorded')
    await command_menu(message)


def register_user_handlers(dp: Dispatcher) -> None:
    # COMMANDS
    dp.register_message_handler(command_start, filters.CommandStart())
    dp.register_message_handler(
        command_calculate_calories, filters.Command('calculate')
    )
    dp.register_message_handler(command_menu, filters.Command('menu'))
    dp.register_message_handler(command_profile, filters.Command('profile'))
    dp.register_message_handler(command_record, filters.Command('record'))

    # CALLBACKS
    dp.register_callback_query_handler(
        callback_calculate_calories, filters.Text(equals='calculate_calorie')
    )
    dp.register_callback_query_handler(
        callback_open_menu, filters.Text(equals='to_menu')
    )
    dp.register_callback_query_handler(callback_record, filters.Text('record'))
    dp.register_callback_query_handler(
        callback_profile, filters.Text('profile')
    )

    # STATES
    # Settings state
    dp.register_callback_query_handler(
        settings_state_language, state=SettingsState.language
    )
    dp.register_callback_query_handler(
        settings_state_time_zone, state=SettingsState.time_zone
    )
    dp.register_callback_query_handler(
        settings_state_unit, state=SettingsState.mass_unit
    )

    # Calculate state
    dp.register_callback_query_handler(
        calculate_state_for_what, state=CalculateState.for_what
    )
    dp.register_callback_query_handler(
        calculate_state_gender, state=CalculateState.gender
    )
    dp.register_message_handler(calculate_state_age, state=CalculateState.age)
    dp.register_message_handler(
        calculate_state_growth, state=CalculateState.growth
    )
    dp.register_message_handler(
        calculate_state_weight, state=CalculateState.weight
    )
    dp.register_callback_query_handler(
        calculate_state_activity, state=CalculateState.activity
    )
    dp.register_callback_query_handler(
        calculate_state_waiting_for_finish,
        state=CalculateState.waiting_for_finish,
    )
    # Record state
    dp.register_message_handler(record_state_weight, state=RecordState.weight)
    dp.register_message_handler(
        record_state_protein, state=RecordState.protein
    )
    dp.register_message_handler(record_state_fat, state=RecordState.fat)
    dp.register_message_handler(record_state_carb, state=RecordState.carb)
